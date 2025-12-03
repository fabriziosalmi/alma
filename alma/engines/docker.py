"""Docker engine implementation."""

from __future__ import annotations

from typing import Any

try:
    import docker
    from docker.errors import DockerException, NotFound
except ImportError:
    docker = None
    DockerException = Exception
    NotFound = Exception

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint


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
        self.client = None

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
            print(f"Failed to list containers: {e}")
            return []

        resources = []
        blueprint_names = {r.name for r in blueprint.resources}

        for container in containers:
            if container.name in blueprint_names:
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
            print(f"Creating container: {resource_def.name}")
            image = resource_def.specs.get("image", "alpine:latest")
            ports = resource_def.specs.get("ports", {})
            env = resource_def.specs.get("env", {})

            try:
                client.containers.run(
                    image, name=resource_def.name, ports=ports, environment=env, detach=True
                )
            except Exception as e:
                print(f"Failed to create container {resource_def.name}: {e}")

        # Update (Recreate)
        for _current_state, resource_def in plan.to_update:
            print(f"Updating container: {resource_def.name}")
            # Docker containers are immutable-ish. Recreate.
            try:
                container = client.containers.get(resource_def.name)
                container.stop()
                container.remove()

                image = resource_def.specs.get("image", "alpine:latest")
                ports = resource_def.specs.get("ports", {})
                env = resource_def.specs.get("env", {})

                client.containers.run(
                    image, name=resource_def.name, ports=ports, environment=env, detach=True
                )
            except Exception as e:
                print(f"Failed to update container {resource_def.name}: {e}")

    async def destroy(self, plan: Plan) -> None:
        """Destroy resources."""
        client = self._get_client()

        for resource_state in plan.to_delete:
            print(f"Destroying container: {resource_state.id}")
            try:
                container = client.containers.get(resource_state.id)
                container.stop()
                container.remove()
            except NotFound:
                print(f"Container {resource_state.id} not found")
            except Exception as e:
                print(f"Failed to destroy container {resource_state.id}: {e}")

    def get_supported_resource_types(self) -> list[str]:
        return ["container"]
