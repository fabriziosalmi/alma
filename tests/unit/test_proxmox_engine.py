"""Unit tests for ProxmoxEngine."""

import pytest
from unittest.mock import AsyncMock, patch

from alma.engines.proxmox import ProxmoxEngine
from alma.engines.base import DeploymentStatus


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
def sample_blueprint() -> dict:
    """Sample blueprint for testing."""
    return {
        "version": "1.0",
        "name": "test-proxmox-blueprint",
        "resources": [
            {
                "type": "compute",
                "name": "test-vm",
                "provider": "proxmox",
                "specs": {
                    "cpu": 2,
                    "memory": "4GB",
                    "storage": "50GB",
                },
            }
        ],
    }


class TestProxmoxEngine:
    """Tests for ProxmoxEngine class."""

    def test_initialization(self, engine: ProxmoxEngine, proxmox_config: dict) -> None:
        """Test engine initialization."""
        assert engine.host == proxmox_config["host"]
        assert engine.username == proxmox_config["username"]
        assert engine.node == proxmox_config["node"]
        assert engine.verify_ssl is False

    async def test_validate_blueprint_valid(
        self, engine: ProxmoxEngine, sample_blueprint: dict
    ) -> None:
        """Test validating a valid blueprint."""
        assert await engine.validate_blueprint(sample_blueprint)

    async def test_validate_blueprint_missing_version(self, engine: ProxmoxEngine) -> None:
        """Test validation fails when version is missing."""
        blueprint = {"name": "test", "resources": []}
        with pytest.raises(ValueError, match="missing 'version' field"):
            await engine.validate_blueprint(blueprint)

    async def test_validate_blueprint_unsupported_resource_type(
        self, engine: ProxmoxEngine
    ) -> None:
        """Test validation fails for unsupported resource types."""
        blueprint = {
            "version": "1.0",
            "name": "test",
            "resources": [
                {
                    "type": "network",  # Not supported by Proxmox engine
                    "name": "test-net",
                }
            ],
        }
        with pytest.raises(ValueError, match="Unsupported resource type"):
            await engine.validate_blueprint(blueprint)

    async def test_validate_blueprint_missing_cpu_spec(self, engine: ProxmoxEngine) -> None:
        """Test validation fails when compute resource missing CPU."""
        blueprint = {
            "version": "1.0",
            "name": "test",
            "resources": [
                {
                    "type": "compute",
                    "name": "test-vm",
                    "specs": {
                        "memory": "4GB",
                        # Missing cpu
                    },
                }
            ],
        }
        with pytest.raises(ValueError, match="missing CPU spec"):
            await engine.validate_blueprint(blueprint)

    def test_parse_memory(self, engine: ProxmoxEngine) -> None:
        """Test memory string parsing."""
        assert engine._parse_memory("4GB") == 4096
        assert engine._parse_memory("512MB") == 512
        assert engine._parse_memory("1024") == 1024
        assert engine._parse_memory("2.5GB") == 2560

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

    async def test_deploy_authentication_failure(
        self, engine: ProxmoxEngine, sample_blueprint: dict
    ) -> None:
        """Test deployment fails when authentication fails."""
        with patch.object(engine, "_authenticate", return_value=False):
            result = await engine.deploy(sample_blueprint)
            assert result.status == DeploymentStatus.FAILED
            assert "authenticate" in result.message.lower()

    async def test_get_state(self, engine: ProxmoxEngine) -> None:
        """Test getting resource state."""
        state = await engine.get_state("100")
        assert state.resource_id == "100"
        assert state.resource_type == "compute"

    async def test_destroy(self, engine: ProxmoxEngine) -> None:
        """Test destroying a resource."""
        result = await engine.destroy("100")
        assert result is True
