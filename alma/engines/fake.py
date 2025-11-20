"""Fake engine for testing and development."""

import asyncio
from typing import Any

from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint


class FakeEngine(Engine):
    """
    Fake engine that simulates infrastructure operations without actual deployment.

    Useful for testing the core state management and planning logic.
    """

    # Class-level storage to persist state across instances for testing purposes
    _resources: dict[str, ResourceState] = {}

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the fake engine."""
        super().__init__(config)
        # Point instance-level resources to the class-level storage
        self.resources = FakeEngine._resources
        self.fail_on_apply = config.get("fail_on_apply", False) if config else False

    @classmethod
    def clear_state(cls) -> None:
        """Clears all resources from the fake engine's state."""
        cls._resources.clear()

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """
        Get simulated state of all resources for a given blueprint.

        In this fake implementation, we assume all resources in the state belong
        to the blueprint being checked. A real engine would use labels or tags.
        """
        await asyncio.sleep(0.01)
        return list(self.resources.values())

    async def apply(self, plan: Plan) -> None:
        """
        Simulate applying a plan to create and update resources.
        """
        if self.fail_on_apply:
            raise RuntimeError("Simulated engine failure on apply.")

        # Simulate creation
        for resource_def in plan.to_create:
            await asyncio.sleep(0.02)
            state = ResourceState(
                id=resource_def.name,
                type=resource_def.type,
                config=resource_def.specs,
            )
            self.resources[resource_def.name] = state

        # Simulate update
        for _current_state, resource_def in plan.to_update:
            await asyncio.sleep(0.02)
            state = ResourceState(
                id=resource_def.name,
                type=resource_def.type,
                config=resource_def.specs,
            )
            self.resources[resource_def.name] = state

        return

    async def destroy(self, plan: Plan) -> None:
        """
        Simulate destroying resources specified in a plan.
        """
        for resource_state in plan.to_delete:
            await asyncio.sleep(0.02)
            if resource_state.id in self.resources:
                del self.resources[resource_state.id]

        return

    def get_supported_resource_types(self) -> list[str]:
        """

        Returns:
            List of all resource types (simulated)
        """
        return ["compute", "network", "storage"]
