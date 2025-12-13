"""Unit tests for ALMA MCP Server."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

# Import the functions to test
# We do this inside tests or at top level if no side effects
from alma.mcp_server import list_resources, deploy_vm, control_vm, get_resource_stats, download_template, list_vms

@pytest.fixture
def mock_engine():
    """Mock the ProxmoxEngine returned by get_engine()."""
    with patch("alma.mcp_server.get_engine") as mock_get:
        engine = MagicMock()
        mock_get.return_value = engine
        yield engine

@pytest.mark.asyncio
async def test_list_resources(mock_engine):
    """Test listing resources."""
    mock_engine.list_resources = AsyncMock(return_value=[{"vmid": 100, "name": "test-vm"}])
    
    result = await list_resources()
    data = json.loads(result)
    
    assert len(data) == 1
    assert data[0]["name"] == "test-vm"
    # Ensure tool wraps result in JSON string
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_get_resource_stats_found(mock_engine):
    """Test getting stats for existing VM."""
    mock_engine.list_resources = AsyncMock(return_value=[
        {"vmid": 100, "name": "vm1"},
        {"vmid": 200, "name": "vm2"}
    ])
    
    result = await get_resource_stats("100")
    data = json.loads(result)
    
    assert data["name"] == "vm1"

@pytest.mark.asyncio
async def test_get_resource_stats_not_found(mock_engine):
    """Test getting stats for non-existent VM."""
    mock_engine.list_resources = AsyncMock(return_value=[])
    
    result = await get_resource_stats("999")
    data = json.loads(result)
    
    assert "error" in data

@pytest.mark.asyncio
async def test_deploy_vm_success(mock_engine):
    """Test VM deployment."""
    mock_engine.apply = AsyncMock()
    
    result = await deploy_vm("new-vm", "ubuntu", cores=4, memory=4096)
    
    assert "Successfully deployed" in result
    mock_engine.apply.assert_called_once()
    
    # Optional: Verify Plan structure
    args, _ = mock_engine.apply.call_args
    plan = args[0]
    assert plan.to_create[0].name == "new-vm"
    assert plan.to_create[0].specs["cpu"] == 4

@pytest.mark.asyncio
async def test_deploy_vm_failure(mock_engine):
    """Test VM deployment failure."""
    mock_engine.apply = AsyncMock(side_effect=RuntimeError("Deploy failed"))
    
    result = await deploy_vm("fail-vm", "ubuntu")
    
    assert "Failed to deploy" in result
    assert "Deploy failed" in result

@pytest.mark.asyncio
async def test_control_vm_start_ssh(mock_engine):
    """Test control_vm using SSH."""
    mock_engine._authenticate = AsyncMock(return_value=True)
    mock_engine.use_ssh = True
    mock_engine._run_ssh_command = AsyncMock()
    
    result = await control_vm("100", "start")
    
    assert "Successfully executed" in result
    mock_engine._run_ssh_command.assert_called_with("qm start 100")

@pytest.mark.asyncio
async def test_control_vm_stop_api(mock_engine):
    """Test control_vm using API."""
    mock_engine._authenticate = AsyncMock(return_value=True)
    mock_engine.use_ssh = False
    mock_engine.node = "pve1"
    
    # Mock list_resources to determine type
    mock_engine.list_resources = AsyncMock(return_value=[
        {"vmid": 100, "type": "lxc"}
    ])
    mock_engine._api_request = AsyncMock()
    
    result = await control_vm("100", "stop")
    
    assert "Successfully executed" in result
    # For LXC, type is lxc
    mock_engine._api_request.assert_called_with("POST", "nodes/pve1/lxc/100/status/stop")

@pytest.mark.asyncio
async def test_control_vm_invalid_action(mock_engine):
    """Test invalid control action."""
    result = await control_vm("100", "dance")
    assert "Invalid action" in result

@pytest.mark.asyncio
async def test_download_template(mock_engine):
    """Test download template."""
    mock_engine.download_template = AsyncMock()
    
    result = await download_template("local", "tmpl.tar.gz")
    
    assert "Successfully downloaded" in result
    mock_engine.download_template.assert_called_with("local", "tmpl.tar.gz")
