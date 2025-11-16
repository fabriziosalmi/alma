"""Fake engine for testing and development."""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ai_cdn.engines.base import (
    Engine,
    DeploymentResult,
    DeploymentStatus,
    ResourceState,
    ResourceStatus,
)


class FakeEngine(Engine):
    """
    Fake engine that simulates infrastructure operations without actual deployment.

    Useful for testing and development.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the fake engine."""
        super().__init__(config)
        self.resources: Dict[str, ResourceState] = {}
        self.deployments: Dict[str, DeploymentResult] = {}
        self.fail_on_deploy = config.get("fail_on_deploy", False) if config else False

    async def validate_blueprint(self, blueprint: Dict[str, Any]) -> bool:
        """
        Validate a blueprint.

        Args:
            blueprint: The system blueprint to validate

        Returns:
            True if valid

        Raises:
            ValueError: If blueprint is missing required fields
        """
        if "version" not in blueprint:
            raise ValueError("Blueprint missing 'version' field")
        if "name" not in blueprint:
            raise ValueError("Blueprint missing 'name' field")
        if "resources" not in blueprint:
            raise ValueError("Blueprint missing 'resources' field")
        return True

    async def deploy(self, blueprint: Dict[str, Any]) -> DeploymentResult:
        """
        Simulate deployment of resources.

        Args:
            blueprint: The system blueprint to deploy

        Returns:
            DeploymentResult with simulated status
        """
        await self.validate_blueprint(blueprint)

        # Simulate deployment time
        await asyncio.sleep(0.1)

        if self.fail_on_deploy:
            return DeploymentResult(
                status=DeploymentStatus.FAILED,
                message="Simulated deployment failure",
                resources_failed=[r.get("name", "unknown") for r in blueprint["resources"]],
            )

        deployment_id = str(uuid4())
        resources_created = []

        for resource in blueprint.get("resources", []):
            resource_id = str(uuid4())
            resource_name = resource.get("name", resource_id)

            # Create fake resource state
            state = ResourceState(
                resource_id=resource_id,
                resource_type=resource.get("type", "unknown"),
                status=ResourceStatus.RUNNING,
                properties=resource.get("specs", {}),
                metadata={
                    "deployment_id": deployment_id,
                    "blueprint_name": blueprint["name"],
                },
            )

            self.resources[resource_id] = state
            resources_created.append(resource_name)

        result = DeploymentResult(
            status=DeploymentStatus.COMPLETED,
            message=f"Successfully deployed {len(resources_created)} resources",
            resources_created=resources_created,
            metadata={"deployment_id": deployment_id},
        )

        self.deployments[deployment_id] = result
        return result

    async def get_state(self, resource_id: str) -> ResourceState:
        """
        Get simulated state of a resource.

        Args:
            resource_id: Unique identifier of the resource

        Returns:
            Current state of the resource

        Raises:
            KeyError: If resource not found
        """
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")
        return self.resources[resource_id]

    async def destroy(self, resource_id: str) -> bool:
        """
        Simulate destroying a resource.

        Args:
            resource_id: Unique identifier of the resource

        Returns:
            True if successful

        Raises:
            KeyError: If resource not found
        """
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        # Simulate destruction time
        await asyncio.sleep(0.05)

        self.resources[resource_id].status = ResourceStatus.DELETED
        return True

    async def rollback(self, deployment_id: str, target_state: Optional[str] = None) -> bool:
        """
        Simulate rollback of a deployment.

        Args:
            deployment_id: Unique identifier of the deployment
            target_state: Optional specific state to rollback to

        Returns:
            True if successful

        Raises:
            KeyError: If deployment not found
        """
        if deployment_id not in self.deployments:
            raise KeyError(f"Deployment {deployment_id} not found")

        # Find all resources for this deployment
        resources_to_rollback = [
            rid
            for rid, state in self.resources.items()
            if state.metadata.get("deployment_id") == deployment_id
        ]

        # Simulate rollback
        await asyncio.sleep(0.1)

        for resource_id in resources_to_rollback:
            self.resources[resource_id].status = ResourceStatus.DELETED

        self.deployments[deployment_id].status = DeploymentStatus.ROLLED_BACK
        return True

    async def health_check(self) -> bool:
        """
        Simulate health check.

        Returns:
            Always returns True for fake engine
        """
        return True

    def get_supported_resource_types(self) -> List[str]:
        """
        Get list of supported resource types.

        Returns:
            List of all resource types (simulated)
        """
        return ["compute", "network", "storage", "service", "load_balancer"]
