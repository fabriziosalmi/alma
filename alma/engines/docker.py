"""Docker engine implementation."""

from __future__ import annotations

import logging
from typing import Any

try:
    import docker
    from docker.errors import DockerException, NotFound, APIError
except ImportError:
    docker = None  # type: ignore[assignment]
    DockerException = Exception  # type: ignore[misc, assignment]
    NotFound = Exception  # type: ignore[misc, assignment]
    APIError = Exception  # type: ignore[misc, assignment]

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint

logger = logging.getLogger(__name__)


class DockerEngine(Engine):
    """
    Engine for Docker.

    Manages containers through the Docker Python SDK.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """
        Initialize Docker engine.

        Args:
            config: Engine configuration
                - base_url: Docker daemon URL (optional)
        """
        super().__init__(config)
        self.base_url = self.config.get("base_url")
        self.client: Any = None

    def _get_client(self) -> Any:
        """Get Docker client."""
        if not docker:
            raise ImportError("docker package is not installed.")

        if not self.client:
            try:
                if self.base_url:
                    self.client = docker.DockerClient(base_url=self.base_url)
                else:
                    self.client = docker.from_env()
            except DockerException as e:
                logger.error(f"Failed to connect to Docker daemon: {e}")
                raise ConnectionError(f"Failed to connect to Docker daemon: {e}") from e
        return self.client

    async def health_check(self) -> bool:
        """Check Docker connectivity."""
        try:
            client = self._get_client()
            client.ping()
            return True
        except Exception:
            return False

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """Get state of all Docker resources."""
        try:
            client = self._get_client()
            containers = client.containers.list(all=True)
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

        resources = []
        blueprint_names = {r.name for r in blueprint.resources}

        for container in containers:
            if container.name in blueprint_names:
                # Map container status to resource state
                resources.append(
                    ResourceState(
                        id=container.name,
                        type="container",
                        config={
                            "image": container.attrs["Config"]["Image"],
                            "status": container.status,
                            "ports": container.attrs["NetworkSettings"]["Ports"],
                        },
                    )
                )
        return resources

    async def apply(self, plan: Plan) -> None:
        """Deploy or update resources."""
        client = self._get_client()

        # Create
        for resource_def in plan.to_create:
            logger.info(f"Creating container: {resource_def.name}")
            image = resource_def.specs.get("image", "alpine:latest")
            ports = resource_def.specs.get("ports", {})
            env = resource_def.specs.get("env", {})
            command = resource_def.specs.get("command", None)

            try:
                client.containers.run(
                    image, 
                    name=resource_def.name, 
                    ports=ports, 
                    environment=env, 
                    command=command,
                    detach=True
                )
                logger.info(f"Container '{resource_def.name}' created successfully.")
            except APIError as e:
                logger.error(f"Docker API Error creating '{resource_def.name}': {e}")
            except Exception as e:
                logger.error(f"Failed to create container '{resource_def.name}': {e}")

        # Update (Recreate)
        for _current_state, resource_def in plan.to_update:
            logger.info(f"Updating container: {resource_def.name}")
            # Docker containers are immutable-ish. Recreate.
            try:
                try:
                    container = client.containers.get(resource_def.name)
                    container.stop()
                    container.remove()
                    logger.info(f"Removed old container '{resource_def.name}'.")
                except NotFound:
                    pass

                image = resource_def.specs.get("image", "alpine:latest")
                ports = resource_def.specs.get("ports", {})
                env = resource_def.specs.get("env", {})
                command = resource_def.specs.get("command", None)

                client.containers.run(
                    image, 
                    name=resource_def.name, 
                    ports=ports, 
                    environment=env,
                    command=command,
                    detach=True
                )
                logger.info(f"Container '{resource_def.name}' updated (recreated).")
            except Exception as e:
                logger.error(f"Failed to update container '{resource_def.name}': {e}")

    async def destroy(self, plan: Plan) -> None:
        """Destroy resources."""
        client = self._get_client()

        for resource_state in plan.to_delete:
            logger.info(f"Destroying container: {resource_state.id}")
            try:
                container = client.containers.get(resource_state.id)
                container.stop()
                container.remove()
                logger.info(f"Container '{resource_state.id}' destroyed.")
            except NotFound:
                logger.warning(f"Container '{resource_state.id}' not found during deletion.")
            except Exception as e:
                logger.error(f"Failed to destroy container '{resource_state.id}': {e}")

    def get_supported_resource_types(self) -> list[str]:
        return ["container"]
