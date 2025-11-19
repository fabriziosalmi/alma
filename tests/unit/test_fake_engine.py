"""Unit tests for FakeEngine."""

import pytest
from alma.engines.fake import FakeEngine
from alma.engines.base import DeploymentStatus, ResourceStatus


@pytest.fixture
def engine() -> FakeEngine:
    """Create a FakeEngine instance."""
    return FakeEngine()


@pytest.fixture
def sample_blueprint() -> dict:
    """Create a sample blueprint."""
    return {
        "version": "1.0",
        "name": "test-blueprint",
        "resources": [
            {
                "type": "compute",
                "name": "web-server",
                "provider": "fake",
                "specs": {"cpu": 2, "memory": "4GB"},
            }
        ],
    }


class TestFakeEngine:
    """Tests for FakeEngine class."""

    async def test_validate_blueprint_valid(self, engine: FakeEngine, sample_blueprint: dict) -> None:
        """Test validating a valid blueprint."""
        assert await engine.validate_blueprint(sample_blueprint)

    async def test_validate_blueprint_missing_version(self, engine: FakeEngine) -> None:
        """Test validation fails when version is missing."""
        blueprint = {"name": "test", "resources": []}
        with pytest.raises(ValueError, match="missing 'version' field"):
            await engine.validate_blueprint(blueprint)

    async def test_validate_blueprint_missing_name(self, engine: FakeEngine) -> None:
        """Test validation fails when name is missing."""
        blueprint = {"version": "1.0", "resources": []}
        with pytest.raises(ValueError, match="missing 'name' field"):
            await engine.validate_blueprint(blueprint)

    async def test_validate_blueprint_missing_resources(self, engine: FakeEngine) -> None:
        """Test validation fails when resources are missing."""
        blueprint = {"version": "1.0", "name": "test"}
        with pytest.raises(ValueError, match="missing 'resources' field"):
            await engine.validate_blueprint(blueprint)

    async def test_deploy_success(self, engine: FakeEngine, sample_blueprint: dict) -> None:
        """Test successful deployment."""
        result = await engine.deploy(sample_blueprint)

        assert result.status == DeploymentStatus.COMPLETED
        assert len(result.resources_created) == 1
        assert "web-server" in result.resources_created
        assert len(result.resources_failed) == 0
        assert "deployment_id" in result.metadata

    async def test_deploy_failure(self, sample_blueprint: dict) -> None:
        """Test deployment failure."""
        engine = FakeEngine(config={"fail_on_deploy": True})
        result = await engine.deploy(sample_blueprint)

        assert result.status == DeploymentStatus.FAILED
        assert len(result.resources_failed) == 1
        assert len(result.resources_created) == 0

    async def test_get_state(self, engine: FakeEngine, sample_blueprint: dict) -> None:
        """Test getting resource state."""
        result = await engine.deploy(sample_blueprint)
        resource_id = list(engine.resources.keys())[0]

        state = await engine.get_state(resource_id)

        assert state.resource_id == resource_id
        assert state.resource_type == "compute"
        assert state.status == ResourceStatus.RUNNING

    async def test_get_state_not_found(self, engine: FakeEngine) -> None:
        """Test getting state of non-existent resource."""
        with pytest.raises(KeyError, match="not found"):
            await engine.get_state("invalid-id")

    async def test_destroy(self, engine: FakeEngine, sample_blueprint: dict) -> None:
        """Test destroying a resource."""
        result = await engine.deploy(sample_blueprint)
        resource_id = list(engine.resources.keys())[0]

        success = await engine.destroy(resource_id)
        assert success

        state = await engine.get_state(resource_id)
        assert state.status == ResourceStatus.DELETED

    async def test_destroy_not_found(self, engine: FakeEngine) -> None:
        """Test destroying non-existent resource."""
        with pytest.raises(KeyError, match="not found"):
            await engine.destroy("invalid-id")

    async def test_rollback(self, engine: FakeEngine, sample_blueprint: dict) -> None:
        """Test rolling back a deployment."""
        result = await engine.deploy(sample_blueprint)
        deployment_id = result.metadata["deployment_id"]

        success = await engine.rollback(deployment_id)
        assert success

        # Check that deployment status is updated
        assert engine.deployments[deployment_id].status == DeploymentStatus.ROLLED_BACK

    async def test_rollback_not_found(self, engine: FakeEngine) -> None:
        """Test rollback of non-existent deployment."""
        with pytest.raises(KeyError, match="not found"):
            await engine.rollback("invalid-id")

    async def test_health_check(self, engine: FakeEngine) -> None:
        """Test health check."""
        assert await engine.health_check()

    def test_get_supported_resource_types(self, engine: FakeEngine) -> None:
        """Test getting supported resource types."""
        types = engine.get_supported_resource_types()
        assert "compute" in types
        assert "network" in types
        assert "storage" in types
