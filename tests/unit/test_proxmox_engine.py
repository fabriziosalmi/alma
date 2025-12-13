"Unit tests for ProxmoxEngine."

from unittest.mock import patch, AsyncMock

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
                "POST", f"nodes/{engine.node}/qemu/101/config", data={"cores": 2, "memory": "4GB"}
            )

    async def test_wait_for_task_success(self, engine: ProxmoxEngine) -> None:
        """Test waiting for task success."""
        with (
            patch.object(engine, "_api_request", return_value={"status": "stopped", "exitstatus": "OK"}) as mock_req,
            patch("asyncio.sleep", return_value=None)
        ):
            result = await engine._wait_for_task("UPID:pve:1234:...")
            assert result is True

    async def test_wait_for_task_failure(self, engine: ProxmoxEngine) -> None:
        """Test waiting for task failure."""
        with (
            patch.object(engine, "_api_request", return_value={"status": "stopped", "exitstatus": "ERROR"}),
            patch("asyncio.sleep", return_value=None)
        ):
            result = await engine._wait_for_task("UPID:pve:1234:...")
            assert result is False

    async def test_wait_for_task_timeout(self, engine: ProxmoxEngine) -> None:
        """Test waiting for task timeout."""
        with (
            patch.object(engine, "_api_request", return_value={"status": "running"}),
            patch("asyncio.sleep", return_value=None)
        ):
            # Short timeout
            result = await engine._wait_for_task("UPID:pve:1234:...", timeout=0.01)
            assert result is False

    async def test_api_circuit_breaker(self, engine: ProxmoxEngine) -> None:
        """Test Circuit Breaker opens after failures."""
        from alma.core.resilience import CircuitBreakerOpenException

        # Mock authentication to pass first
        with patch.object(engine, "_authenticate", return_value=True):
            engine.ticket = "ticket"
            engine.csrf_token = "token"

            # 1. Fail 5 times (Default Threshold)
            with patch("httpx.AsyncClient.request", side_effect=IndexError("Network Error")):
                for _ in range(5):
                    try:
                        await engine._api_request("GET", "cluster/status")
                    except Exception:
                        pass
            
            # 2. Check Circuit is Open
            assert engine.circuit_breaker.state.value == "OPEN"
            
            # 3. Next call should raise CircuitBreakerOpenException immediately (wrapped as ConnectionError)
            with pytest.raises(ConnectionError, match="Circuit Broken"):
                await engine._api_request("GET", "cluster/status")

    async def test_download_template_api(self, engine: ProxmoxEngine) -> None:
        """Test download_template via API path."""
        # Mock API success for valid template
        with (
            patch.object(engine, "_authenticate", return_value=True),
            patch.object(engine, "_api_request", return_value="UPID:node:123:download") as mock_req,
            patch.object(engine, "_wait_for_task", return_value=True)
        ):
            success = await engine.download_template("local", "alpine")
            assert success is True
            mock_req.assert_called_once()
            args, kwargs = mock_req.call_args
            assert kwargs["data"]["filename"] == "alpine-3.22-default_20250617_amd64.tar.xz"

    async def test_download_template_unknown(self, engine: ProxmoxEngine) -> None:
        """Test download_template returns False for unknown template."""
        success = await engine.download_template("local", "unknown-distro")
        assert success is False

    @patch("asyncio.create_subprocess_exec")
    async def test_run_ssh_command(self, mock_exec, engine: ProxmoxEngine) -> None:
        """Test SSH command execution."""
        # Mock successful process
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output\n", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        output = await engine._run_ssh_command(["echo", "hello"])
        assert output == "output"
        
        # Verify SSH args safe from injection (list format)
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert "ssh" in args[0]
        assert "-o" in args
        assert "BatchMode=yes" in args
        assert "echo" in args

    @patch("asyncio.create_subprocess_exec")
    async def test_run_ssh_command_failure(self, mock_exec, engine: ProxmoxEngine) -> None:
        """Test SSH command failure."""
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"permission denied")
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        with pytest.raises(Exception, match="SSH Command failed"):
            await engine._run_ssh_command(["ls"])

    async def test_get_vm_by_name_lxc(self, engine: ProxmoxEngine) -> None:
        """Test finding LXC container by name."""
        mock_lxc = [{"vmid": 102, "name": "my-container", "status": "running"}]
        
        async def api_side_effect(method, endpoint, data=None):
            if "qemu" in endpoint:
                return []
            if "lxc" in endpoint:
                return mock_lxc
            return []

        with patch.object(engine, "_api_request", side_effect=api_side_effect):
            result = await engine._get_vm_by_name("my-container")
            assert result is not None
            assert result["vmid"] == 102
            assert result["type"] == "lxc"

    async def test_list_resources(self, engine: ProxmoxEngine) -> None:
        """Test listing all resources."""
        # Mock QEMU and LXC returns
        async def api_side_effect(method, endpoint, data=None):
            if "qemu" in endpoint:
                return [{"vmid": 101, "name": "vm1"}]
            if "lxc" in endpoint:
                return [{"vmid": 102, "name": "ct1"}]
            return []

        with patch.object(engine, "_api_request", side_effect=api_side_effect):
            resources = await engine.list_resources()
            assert len(resources) == 2
            assert resources[0]["type"] == "qemu"
            assert resources[1]["type"] == "lxc"

