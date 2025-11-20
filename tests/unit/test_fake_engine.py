"""Unit tests for FakeEngine."""
import pytest
from alma.core.state import Plan, ResourceState
from alma.engines.fake import FakeEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition


@pytest.fixture(autouse=True)
def engine() -> FakeEngine:
    """Create a FakeEngine instance and clear its state."""
    engine = FakeEngine()
    engine.clear_state()
    return engine


@pytest.fixture
def sample_blueprint() -> SystemBlueprint:
    """Create a sample blueprint."""
    return SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        version="1.0",
        name="test-blueprint",
        resources=[
            ResourceDefinition(
                type="compute",
                name="web-server",
                provider="fake",
                specs={"cpu": 2, "memory": "4GB"},
            )
        ],
    )


class TestFakeEngine:
    """Tests for FakeEngine class."""

    async def test_apply_create(
        self, engine: FakeEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test successful creation of resources."""
        plan = Plan(to_create=sample_blueprint.resources)
        await engine.apply(plan)

        state = await engine.get_state(sample_blueprint)
        assert len(state) == 1
        assert state[0].id == "web-server"
        assert state[0].config["cpu"] == 2

    async def test_apply_update(
        self, engine: FakeEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test successful update of resources."""
        # First, create the resource
        plan_create = Plan(to_create=sample_blueprint.resources)
        await engine.apply(plan_create)

        # Now, create a plan to update it
        current_state = await engine.get_state(sample_blueprint)
        updated_resource = sample_blueprint.resources[0].model_copy()
        updated_resource.specs["cpu"] = 4
        plan_update = Plan(to_update=[(current_state[0], updated_resource)])

        await engine.apply(plan_update)

        new_state = await engine.get_state(sample_blueprint)
        assert len(new_state) == 1
        assert new_state[0].config["cpu"] == 4

    async def test_destroy(self, engine: FakeEngine, sample_blueprint: SystemBlueprint) -> None:
        """Test destroying a resource."""
        # First, create the resource
        plan_create = Plan(to_create=sample_blueprint.resources)
        await engine.apply(plan_create)
        assert len(await engine.get_state(sample_blueprint)) == 1

        # Now, destroy it
        current_state = await engine.get_state(sample_blueprint)
        plan_destroy = Plan(to_delete=current_state)
        await engine.destroy(plan_destroy)

        assert len(await engine.get_state(sample_blueprint)) == 0

    async def test_get_state_empty(
        self, engine: FakeEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test getting state when no resources exist."""
        state = await engine.get_state(sample_blueprint)
        assert state == []

    async def test_apply_failure(self, sample_blueprint: SystemBlueprint) -> None:
        """Test deployment failure."""
        engine = FakeEngine(config={"fail_on_apply": True})
        plan = Plan(to_create=sample_blueprint.resources)
        with pytest.raises(RuntimeError, match="Simulated engine failure on apply"):
            await engine.apply(plan)

    async def test_health_check(self, engine: FakeEngine) -> None:
        """Test health check."""
        assert await engine.health_check()

    def test_get_supported_resource_types(self, engine: FakeEngine) -> None:
        """Test getting supported resource types."""
        types = engine.get_supported_resource_types()
        assert "compute" in types
        assert "network" in types
        assert "storage" in types
