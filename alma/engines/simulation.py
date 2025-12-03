"""Simulation engine for dry-runs and non-production environments."""

from __future__ import annotations

import asyncio
from typing import Any

from alma.core.state import Plan, ResourceState
from alma.core.state import Plan, ResourceState
from alma.engines.base import Engine
from alma.schemas.blueprint import SystemBlueprint, DeploymentResponse


class SimulationEngine(Engine):
    """
    Simulation engine that mimics infrastructure operations.
    
    Used for:
    1. Dry-run deployments
    2. Testing deployment logic without cloud credentials
    3. Demonstrations
    
    This engine maintains an in-memory state of resources.
    """

    # In-memory storage for simulation
    _simulated_resources: dict[str, ResourceState] = {}

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the simulation engine."""
        super().__init__(config)
        self.resources = SimulationEngine._simulated_resources
        self.simulate_latency = True

    @classmethod
    def reset(cls) -> None:
        """Reset the simulation state."""
        cls._simulated_resources.clear()

    async def get_state(self, blueprint: SystemBlueprint) -> list[ResourceState]:
        """Get simulated state of resources."""
        if self.simulate_latency:
            await asyncio.sleep(0.01)
        return list(self.resources.values())

    async def apply(self, plan: Plan) -> None:
        """Simulate applying a plan."""
        # Simulate creation
        for resource_def in plan.to_create:
            if self.simulate_latency:
                await asyncio.sleep(0.02)
            
            state = ResourceState(
                id=resource_def.name,
                type=resource_def.type,
                config=resource_def.specs,
            )
            self.resources[resource_def.name] = state

        # Simulate update
        for _current_state, resource_def in plan.to_update:
            if self.simulate_latency:
                await asyncio.sleep(0.02)
            
            state = ResourceState(
                id=resource_def.name,
                type=resource_def.type,
                config=resource_def.specs,
            )
            self.resources[resource_def.name] = state

    async def destroy(self, plan: Plan) -> None:
        """Simulate destroying resources."""
        for resource_state in plan.to_delete:
            if self.simulate_latency:
                await asyncio.sleep(0.02)
            
            if resource_state.id in self.resources:
                del self.resources[resource_state.id]

    def get_supported_resource_types(self) -> list[str]:
        """Return supported resource types."""
        return ["compute", "network", "storage", "database", "cache"]

    async def validate_blueprint(self, blueprint: dict[str, Any]) -> bool:
        """Validate a blueprint."""
        if self.simulate_latency:
            await asyncio.sleep(0.01)
        return True

    async def deploy(self, blueprint: dict[str, Any]) -> DeploymentResponse:
        """Deploy a blueprint."""
        if self.simulate_latency:
            await asyncio.sleep(0.05)
        
        return DeploymentResponse(
            deployment_id="sim-deploy-123",
            status="completed",
            message="Simulation deployment successful",
            plan_summary="Created 3 resources (simulated)",
            resources_created=["sim-vm-1", "sim-db-1", "sim-net-1"],
        )

    async def rollback(self, deployment_id: str, target: str | None = None) -> bool:
        """Rollback a deployment."""
        if self.simulate_latency:
            await asyncio.sleep(0.05)
        return True
