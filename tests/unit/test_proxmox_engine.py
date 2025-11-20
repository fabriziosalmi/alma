"Unit tests for ProxmoxEngine."

from unittest.mock import MagicMock, patch

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
        with patch.object(engine, "_authenticate", return_value=True):
            state = await engine.get_state(sample_blueprint)
            assert state == []

    async def test_apply_create(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test apply for resource creation."""
        plan = Plan(to_create=sample_blueprint.resources)
        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            await engine.apply(plan)
            mock_print.assert_called_with("Fake creating resource: test-vm")

    async def test_destroy(self, engine: ProxmoxEngine) -> None:
        """Test destroying a resource."""
        resource_state = ResourceState(id="vm/101", type="compute", config={})
        plan = Plan(to_delete=[resource_state])
        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            await engine.destroy(plan)
            mock_print.assert_called_with("Fake deleting resource: vm/101")

    async def test_destroy_authentication_failure(self, engine: ProxmoxEngine) -> None:
        """Test destroy fails when authentication fails."""
        resource_state = ResourceState(id="vm/101", type="compute", config={})
        plan = Plan(to_delete=[resource_state])
        with patch.object(engine, "_authenticate", return_value=False):
            with pytest.raises(ConnectionError, match="Failed to authenticate"):
                await engine.destroy(plan)

    @pytest.mark.asyncio
    async def test_authenticate_success(self, engine: ProxmoxEngine) -> None:
        """Test successful authentication."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "ticket": "test-ticket-123",
                "CSRFPreventionToken": "test-csrf-token-456",
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            result = await engine._authenticate()
            assert result is True
            assert engine.ticket == "test-ticket-123"
            assert engine.csrf_token == "test-csrf-token-456"

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, engine: ProxmoxEngine) -> None:
        """Test failed authentication."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception(
                "Connection refused"
            )
            result = await engine._authenticate()
            assert result is False
            assert engine.ticket is None
            assert engine.csrf_token is None

    @pytest.mark.asyncio
    async def test_api_request_with_authentication(self, engine: ProxmoxEngine) -> None:
        """Test API request with automatic authentication."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"status": "ok"}}
        mock_response.raise_for_status = MagicMock()

        with patch.object(engine, "_authenticate", return_value=True) as mock_auth:
            engine.ticket = None  # Force authentication
            with patch("httpx.AsyncClient") as mock_client:
                mock_client.return_value.__aenter__.return_value.request.return_value = (
                    mock_response
                )
                result = await engine._api_request("GET", "nodes/pve/status")
                assert result == {"status": "ok"}
                mock_auth.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_request_with_existing_ticket(self, engine: ProxmoxEngine) -> None:
        """Test API request with existing ticket."""
        engine.ticket = "existing-ticket"
        engine.csrf_token = "existing-csrf"

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"nodes": []}}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response
            result = await engine._api_request("GET", "nodes")
            assert result == {"nodes": []}

    async def test_apply_update(
        self, engine: ProxmoxEngine, sample_blueprint: SystemBlueprint
    ) -> None:
        """Test apply for resource updates."""
        old_state = ResourceState(id="vm/101", type="compute", config={"cpu": 1})
        plan = Plan(to_update=[(old_state, sample_blueprint.resources[0])])
        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch("builtins.print") as mock_print,
        ):
            await engine.apply(plan)
            mock_print.assert_called_with("Fake updating resource: test-vm")
