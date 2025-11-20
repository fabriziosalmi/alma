"""
FakeEngine - Mock engine for testing
"""
import asyncio
from typing import Dict, Any
from aicdn.engines.base import BaseEngine, DeployResult, DeployStatus, ActionStatus, ResourceStatus


class FakeEngine(BaseEngine):
    """
    Fake engine implementation for testing purposes.

    This engine simulates deployments without actually creating any resources.
    Useful for testing the controller logic and API.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        super().__init__(config)
        self._deployed_resources: Dict[str, Dict[str, Any]] = {}

    async def deploy(self, resource_config: Dict[str, Any]) -> DeployResult:
        """
        Simulate a deployment with a short delay
        """
        resource_name = resource_config.get("name", "unknown")

        # Simulate deployment delay
        await asyncio.sleep(0.5)

        # Store the "deployed" resource
        self._deployed_resources[resource_name] = {
            "config": resource_config,
            "status": "running",
            "endpoint": f"http://fake-{resource_name}.local",
        }

        return DeployResult(
            status=DeployStatus.COMPLETED,
            endpoint=f"http://fake-{resource_name}.local",
            message=f"Successfully deployed {resource_name} (fake)",
            metadata={"engine": "fake", "resource_name": resource_name},
        )

    async def destroy(self, resource_config: Dict[str, Any]) -> ActionStatus:
        """
        Simulate resource destruction
        """
        resource_name = resource_config.get("name", "unknown")

        # Simulate delay
        await asyncio.sleep(0.3)

        if resource_name in self._deployed_resources:
            del self._deployed_resources[resource_name]
            return ActionStatus(
                success=True, message=f"Successfully destroyed {resource_name} (fake)"
            )

        return ActionStatus(success=False, message=f"Resource {resource_name} not found")

    async def get_status(self, resource_config: Dict[str, Any]) -> ResourceStatus:
        """
        Get status of a fake resource
        """
        resource_name = resource_config.get("name", "unknown")

        if resource_name in self._deployed_resources:
            resource = self._deployed_resources[resource_name]
            return ResourceStatus(
                state="running",
                ready=True,
                endpoint=resource.get("endpoint"),
                metadata={"engine": "fake"},
            )

        return ResourceStatus(state="not_found", ready=False, metadata={"engine": "fake"})

    async def dry_run(self, resource_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show what would be deployed
        """
        resource_name = resource_config.get("name", "unknown")

        return {
            "action": "create",
            "resource_name": resource_name,
            "changes": {
                "add": [
                    f"+ fake_resource.{resource_name}",
                    f"  endpoint: http://fake-{resource_name}.local",
                ]
            },
            "note": "This is a fake engine - no real resources will be created",
        }
