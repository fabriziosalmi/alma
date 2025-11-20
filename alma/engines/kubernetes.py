"""Kubernetes engine for managing cluster resources."""

import logging
from typing import Any, Dict, List, Optional

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client.exceptions import ApiException

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint

logger = logging.getLogger(__name__)

# Standard label to be applied to all resources managed by ALMA
alma_BLUEPRINT_LABEL = "ALMA-blueprint"


class KubernetesEngine(Engine):
    """
    Engine for Kubernetes.

    Manages Deployments, Services, and other resources through the Kubernetes API.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config_dict)
        self.namespace = self.config.get("namespace", "default")
        self.api_client: Optional[client.ApiClient] = None

    async def _initialize_clients(self) -> None:
        """Load Kubernetes configuration and initialize API clients."""
        if self.api_client:
            return
        try:
            # Try loading from a cluster's service account first
            config.load_incluster_config()
        except config.ConfigException:
            # Fall back to kube config file
            await config.load_kube_config()

        self.api_client = client.ApiClient()
        self.apps_v1 = client.AppsV1Api(self.api_client)
        self.core_v1 = client.CoreV1Api(self.api_client)

    async def health_check(self) -> bool:
        """Check if the engine can connect to the Kubernetes API."""
        try:
            await self._initialize_clients()
            await self.core_v1.get_api_resources()
            logger.info("Kubernetes API health check successful.")
            return True
        except Exception as e:
            logger.error(f"Kubernetes API health check failed: {e}", exc_info=True)
            return False

    async def get_state(self, blueprint: SystemBlueprint) -> List[ResourceState]:
        """
        Get the current state of all resources managed by a blueprint in the cluster.
        """
        await self._initialize_clients()
        label_selector = f"{alma_BLUEPRINT_LABEL}={blueprint.name}"
        states: List[ResourceState] = []

        # Get Deployments
        try:
            deployments = await self.apps_v1.list_namespaced_deployment(
                namespace=self.namespace, label_selector=label_selector
            )
            for dep in deployments.items:
                states.append(self._deployment_to_resource_state(dep))
        except ApiException as e:
            logger.error(f"Error listing deployments: {e}")
            raise

        # Get Services
        try:
            services = await self.core_v1.list_namespaced_service(
                namespace=self.namespace, label_selector=label_selector
            )
            for svc in services.items:
                states.append(self._service_to_resource_state(svc))
        except ApiException as e:
            logger.error(f"Error listing services: {e}")
            raise

        return states

    async def apply(self, plan: Plan) -> None:
        """Apply a plan to create or update Kubernetes resources."""
        await self._initialize_clients()

        # We can process creates and updates together
        for resource in plan.to_create + [res for _, res in plan.to_update]:
            try:
                if resource.type == "compute":
                    await self._apply_deployment(resource)
                elif resource.type == "network":
                    await self._apply_service(resource)
                else:
                    logger.warning(
                        f"Resource type '{resource.type}' is not supported by KubernetesEngine."
                    )
            except Exception as e:
                logger.error(f"Failed to apply resource '{resource.name}': {e}", exc_info=True)
                # In a real scenario, we might want to collect failures and report them
                raise

    async def destroy(self, plan: Plan) -> None:
        """Destroy Kubernetes resources based on a plan."""
        await self._initialize_clients()

        for resource_state in plan.to_delete:
            try:
                if resource_state.type == "compute":
                    await self.apps_v1.delete_namespaced_deployment(
                        name=resource_state.id, namespace=self.namespace
                    )
                    logger.info(f"Deleted Deployment: {resource_state.id}")
                elif resource_state.type == "network":
                    await self.core_v1.delete_namespaced_service(
                        name=resource_state.id, namespace=self.namespace
                    )
                    logger.info(f"Deleted Service: {resource_state.id}")
            except ApiException as e:
                if e.status == 404:
                    logger.warning(
                        f"Resource '{resource_state.id}' not found for deletion, skipping."
                    )
                else:
                    logger.error(f"Failed to delete resource '{resource_state.id}': {e}")
                    raise

    # --- Helper methods for applying resources ---

    async def _apply_deployment(self, resource: ResourceDefinition) -> None:
        """Create or patch a Deployment."""
        deployment_body = self._construct_deployment(resource)
        try:
            await self.apps_v1.read_namespaced_deployment(
                name=resource.name, namespace=self.namespace
            )
            await self.apps_v1.patch_namespaced_deployment(
                name=resource.name, namespace=self.namespace, body=deployment_body
            )
            logger.info(f"Patched Deployment: {resource.name}")
        except ApiException as e:
            if e.status == 404:
                await self.apps_v1.create_namespaced_deployment(
                    namespace=self.namespace, body=deployment_body
                )
                logger.info(f"Created Deployment: {resource.name}")
            else:
                raise

    async def _apply_service(self, resource: ResourceDefinition) -> None:
        """Create or patch a Service."""
        service_body = self._construct_service(resource)
        try:
            await self.core_v1.read_namespaced_service(name=resource.name, namespace=self.namespace)
            # Service updates can be tricky, for simple cases, patch might work.
            # A more robust solution might delete and recreate.
            await self.core_v1.patch_namespaced_service(
                name=resource.name, namespace=self.namespace, body=service_body
            )
            logger.info(f"Patched Service: {resource.name}")
        except ApiException as e:
            if e.status == 404:
                await self.core_v1.create_namespaced_service(
                    namespace=self.namespace, body=service_body
                )
                logger.info(f"Created Service: {resource.name}")
            else:
                raise

    # --- Helper methods for constructing K8s objects ---

    def _construct_deployment(self, resource: ResourceDefinition) -> client.V1Deployment:
        """Constructs a V1Deployment object from a ResourceDefinition."""
        specs = resource.specs
        name = resource.name
        labels = {
            alma_BLUEPRINT_LABEL: resource.metadata.get("blueprint_name", "unknown"),
            "app": name,
        }

        container = client.V1Container(
            name=name,
            image=specs.get("image"),
            ports=[client.V1ContainerPort(container_port=specs.get("port", 80))],
        )

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels),
            spec=client.V1PodSpec(containers=[container]),
        )

        spec = client.V1DeploymentSpec(
            replicas=specs.get("replicas", 1),
            template=template,
            selector=client.V1LabelSelector(match_labels=labels),
        )

        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name, labels=labels, namespace=self.namespace),
            spec=spec,
        )

    def _construct_service(self, resource: ResourceDefinition) -> client.V1Service:
        """Constructs a V1Service object from a ResourceDefinition."""
        specs = resource.specs
        name = resource.name

        # Service selects pods based on the 'app' label of a 'compute' resource.
        # This assumes a convention where a network resource 'x-svc' targets a compute resource 'x'.
        target_app = specs.get("selector")
        if not target_app:
            raise ValueError(f"Network resource '{name}' is missing a 'selector' in its specs.")

        labels = {
            alma_BLUEPRINT_LABEL: resource.metadata.get("blueprint_name", "unknown"),
            "app": name,
        }

        selector = {"app": target_app}

        port = client.V1ServicePort(
            protocol="TCP",
            port=specs.get("port", 80),
            target_port=specs.get("target_port", specs.get("port", 80)),
        )

        spec = client.V1ServiceSpec(
            selector=selector,
            ports=[port],
            type=specs.get("service_type", "LoadBalancer"),
        )

        return client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name, labels=labels, namespace=self.namespace),
            spec=spec,
        )

    # --- Helper methods for converting K8s objects to ResourceState ---

    def _deployment_to_resource_state(self, dep: client.V1Deployment) -> ResourceState:
        """Converts a V1Deployment to a ResourceState."""
        return ResourceState(
            id=dep.metadata.name,
            type="compute",
            config={
                "replicas": dep.spec.replicas,
                "image": dep.spec.template.spec.containers[0].image,
                "port": dep.spec.template.spec.containers[0].ports[0].container_port,
            },
        )

    def _service_to_resource_state(self, svc: client.V1Service) -> ResourceState:
        """Converts a V1Service to a ResourceState."""
        # This is a simplification; a real conversion might be more complex
        return ResourceState(
            id=svc.metadata.name,
            type="network",
            config={
                "selector": list(svc.spec.selector.values())[0] if svc.spec.selector else None,
                "port": svc.spec.ports[0].port,
                "target_port": svc.spec.ports[0].target_port,
                "service_type": svc.spec.type,
            },
        )

    def get_supported_resource_types(self) -> List[str]:
        return ["compute", "network"]
