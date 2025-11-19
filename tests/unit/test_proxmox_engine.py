"Unit tests for ProxmoxEngine."

import pytest
from unittest.mock import patch, MagicMock
from alma.core.state import Plan, ResourceState
from alma.engines.proxmox import ProxmoxEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition


@pytest.fixture
def proxmox_config() -> dict:
    """Proxmox engine configuration."""
    return {
        "host": "https://proxmox.example.com:8006",
        "username": "test@pam",
        "password": "test-password",
        "node": "pve-test",
        "verify_ssl": False,
    }


@pytest.fixture
def engine(proxmox_config: dict) -> ProxmoxEngine:
    """Create ProxmoxEngine instance."""
    return ProxmoxEngine(config=proxmox_config)


@pytest.fixture
def sample_blueprint() -> SystemBlueprint:
    """Sample blueprint for testing."""
    return SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        version="1.0",
        name="test-proxmox-blueprint",
        resources=[
            ResourceDefinition(
                type="compute",
                name="test-vm",
                provider="proxmox",
                specs={
                    "cpu": 2,
                    "memory": "4GB",
                    "storage": "50GB",
                },
            )
        ],
    )


class TestProxmoxEngine:
    """Tests for ProxmoxEngine class."""

    def test_initialization(self, engine: ProxmoxEngine, proxmox_config: dict) -> None:
        """Test engine initialization."""
        assert engine.host == proxmox_config["host"]
        assert engine.username == proxmox_config["username"]
        assert engine.node == proxmox_config["node"]
        assert engine.verify_ssl is False

    async def test_health_check_success(self, engine: ProxmoxEngine) -> None:
        """Test successful health check."""
        with patch.object(engine, "_authenticate", return_value=True):
            assert await engine.health_check()

    async def test_health_check_failure(self, engine: ProxmoxEngine) -> None:
        """Test failed health check."""
        with patch.object(engine, "_authenticate", side_effect=Exception("Connection failed")):
            assert not await engine.health_check()

    def test_get_supported_resource_types(self, engine: ProxmoxEngine) -> None:
        """Test getting supported resource types."""
        types = engine.get_supported_resource_types()
        assert "compute" in types
        assert "storage" in types
        assert "network" not in types

    async def test_apply_authentication_failure(self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint) -> None:
        """Test deployment fails when authentication fails."""
        plan = Plan(to_create=sample_blueprint.resources)
        with patch.object(engine, "_authenticate", return_value=False):
            with pytest.raises(ConnectionError, match="Failed to authenticate"):
                await engine.apply(plan)

    async def test_get_state_empty(self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint) -> None:
        """Test getting state when no resources exist."""
        with patch.object(engine, "_authenticate", return_value=True):
            state = await engine.get_state(sample_blueprint)
            assert state == []

    async def test_apply_create(self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint) -> None:
        """Test apply for resource creation."""
        plan = Plan(to_create=sample_blueprint.resources)
        with patch.object(engine, "_authenticate", return_value=True), \
             patch('builtins.print') as mock_print:
            await engine.apply(plan)
            mock_print.assert_called_with("Fake creating resource: test-vm")
            
    async def test_destroy(self, engine: ProxmoxEngine) -> None:
        """Test destroying a resource."""
        resource_state = ResourceState(id="vm/101", type="compute", config={})
        plan = Plan(to_delete=[resource_state])
        with patch.object(engine, "_authenticate", return_value=True), \
             patch('builtins.print') as mock_print:
            await engine.destroy(plan)
            mock_print.assert_called_with("Fake deleting resource: vm/101")