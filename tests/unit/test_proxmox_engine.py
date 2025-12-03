"Unit tests for ProxmoxEngine."

from unittest.mock import patch

import pytest

from alma.core.state import Plan, ResourceState
from alma.engines.proxmox import ProxmoxEngine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint


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

    async def test_apply_authentication_failure(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test deployment fails when authentication fails."""
        plan = Plan(to_create=sample_blueprint.resources)
        with patch.object(engine, "_authenticate", return_value=False):
            with pytest.raises(ConnectionError, match="Failed to authenticate"):
                await engine.apply(plan)

    async def test_get_state_empty(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test getting state when no resources exist."""
        with patch.object(engine, "_api_request", return_value=[]):
            state = await engine.get_state(sample_blueprint)
            assert state == []

    async def test_apply_create(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test apply for resource creation."""
        plan = Plan(to_create=sample_blueprint.resources)

        # Mock template lookup
        mock_template = {"vmid": 100, "name": "ubuntu-template", "type": "qemu"}

        # Mock API responses
        async def api_side_effect(method, endpoint, data=None):
            if endpoint == "cluster/nextid":
                return 101
            if endpoint == f"nodes/{engine.node}/qemu":
                return [mock_template]
            if endpoint == f"nodes/{engine.node}/lxc":
                return []
            return {}

        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch.object(engine, "_api_request", side_effect=api_side_effect) as mock_req,
        ):
            # Add template spec to resource
            sample_blueprint.resources[0].specs["template"] = "ubuntu-template"

            await engine.apply(plan)

            # Verify clone call
            mock_req.assert_any_call(
                "POST",
                f"nodes/{engine.node}/qemu/100/clone",
                data={"newid": 101, "name": "test-vm", "full": 1},
            )
            # Verify start call
            mock_req.assert_any_call("POST", f"nodes/{engine.node}/qemu/101/status/start")

    async def test_destroy(self, engine: ProxmoxEngine) -> None:
        """Test destroying a resource."""
        resource_state = ResourceState(id="test-vm", type="compute", config={})
        plan = Plan(to_delete=[resource_state])

        mock_vm = {"vmid": 101, "name": "test-vm", "type": "qemu"}

        async def api_side_effect(method, endpoint, data=None):
            if endpoint == f"nodes/{engine.node}/qemu":
                return [mock_vm]
            if endpoint == f"nodes/{engine.node}/lxc":
                return []
            return {}

        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch.object(engine, "_api_request", side_effect=api_side_effect) as mock_req,
        ):
            await engine.destroy(plan)

            # Verify stop call
            mock_req.assert_any_call("POST", f"nodes/{engine.node}/qemu/101/status/stop")
            # Verify delete call
            mock_req.assert_any_call("DELETE", f"nodes/{engine.node}/qemu/101")

    async def test_apply_update(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test apply for resource updates."""
        old_state = ResourceState(id="test-vm", type="compute", config={"cores": 1})
        plan = Plan(to_update=[(old_state, sample_blueprint.resources[0])])

        mock_vm = {"vmid": 101, "name": "test-vm", "type": "qemu"}

        async def api_side_effect(method, endpoint, data=None):
            if endpoint == f"nodes/{engine.node}/qemu":
                return [mock_vm]
            if endpoint == f"nodes/{engine.node}/lxc":
                return []
            return {}

        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch.object(engine, "_api_request", side_effect=api_side_effect) as mock_req,
        ):
            await engine.apply(plan)

            # Verify config update
            mock_req.assert_any_call(
                "POST", f"nodes/{engine.node}/qemu/101/config", data={"cores": 2}
            )
