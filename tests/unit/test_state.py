"""Unit tests for state module."""

import pytest
from alma.core.state import Plan, ResourceState
from alma.schemas.blueprint import ResourceDefinition


class TestResourceState:
    def test_resource_state_creation(self):
        """Test creating a ResourceState."""
        state = ResourceState(
            id="vm-001",
            type="compute",
            config={"cpu": 2, "memory": "4GB"}
        )
        assert state.id == "vm-001"
        assert state.type == "compute"
        assert state.config["cpu"] == 2


class TestPlan:
    def test_empty_plan(self):
        """Test creating an empty plan."""
        plan = Plan()
        assert len(plan.to_create) == 0
        assert len(plan.to_update) == 0
        assert len(plan.to_delete) == 0
    
    def test_plan_with_creates(self):
        """Test plan with resources to create."""
        resource = ResourceDefinition(
            name="test-vm",
            type="compute",
            provider="fake",
            specs={"cpu": 2}
        )
        plan = Plan(to_create=[resource])
        assert len(plan.to_create) == 1
        assert plan.to_create[0].name == "test-vm"
    
    def test_plan_with_updates(self):
        """Test plan with resources to update."""
        current = ResourceState(id="vm-001", type="compute", config={})
        desired = ResourceDefinition(
            name="vm-001",
            type="compute",
            provider="fake",
            specs={"cpu": 4}
        )
        plan = Plan(to_update=[(current, desired)])
        assert len(plan.to_update) == 1
        assert plan.to_update[0][0].id == "vm-001"
        assert plan.to_update[0][1].specs["cpu"] == 4
    
    def test_plan_with_deletes(self):
        """Test plan with resources to delete."""
        state = ResourceState(id="vm-001", type="compute", config={})
        plan = Plan(to_delete=[state])
        assert len(plan.to_delete) == 1
        assert plan.to_delete[0].id == "vm-001"
