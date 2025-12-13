"""Integration tests for Proxmox Engine Resilience (Mocked API)."""

import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from alma.engines.proxmox import ProxmoxEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition
from datetime import datetime

@pytest.fixture
def engine():
    return ProxmoxEngine(config={"node": "test-node", "url": "https://test:8006", "token": "user@pam:token"})

@pytest.fixture
def blueprint():
    return SystemBlueprint(
        id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="integration-test-sys",
        resources=[
            ResourceDefinition(
                name="app-vm",
                type="compute",
                provider="proxmox",
                specs={"cpu": 2, "memory": 2048, "template": "ubuntu"}
            )
        ]
    )

class TestProxmoxResilienceIntegration:

    @pytest.mark.asyncio
    async def test_auth_failure_handling(self, engine, blueprint):
        """Verify engine fails gracefully on auth error."""
        
        # When _authenticate calls client.post -> response.raise_for_status()
        # We need mock_post to return a response that raises on raise_for_status
        
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=MagicMock(status_code=401))
        
        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            # Attempt apply
            # _authenticate catches the exception and returns False
            # then apply/reconcile checks if not authenticated -> raises ConnectionError
            
            with pytest.raises(ConnectionError, match="Failed to authenticate"):
                await engine.apply(MagicMock())

    @pytest.mark.asyncio
    async def test_api_timeout_circuit_breaker_integration(self, engine, blueprint):
        """Verify repeated timeouts trigger Circuit Breaker in 'real' flow."""
        
        # We need to bypass Auth so we hit the Circuit Breaker in _api_request
        with patch.object(engine, "_authenticate", return_value=True):
            engine.ticket = "mock-ticket"
            engine.csrf_token = "mock-token"
            
            # Mock Timeout Exception in _api_request -> client.request
            with patch("httpx.AsyncClient.request", side_effect=asyncio.TimeoutError("Timeout")):
                
                # 1. Trigger failures until threshold (5)
                # We use internal _api_request directly to ensure we don't catch exception in get_state
                # Or we assert that get_state returns empty but CB state changes
                
                for i in range(5):
                    try:
                        await engine._api_request("GET", "cluster/status")
                    except Exception:
                        pass
                
                # 2. Verify Circuit is OPEN
                assert engine.circuit_breaker.state.value == "OPEN"
                
                # 3. Next call should fail FAST (no network call)
                with pytest.raises(ConnectionError, match="Circuit Broken"):
                    await engine._api_request("GET", "cluster/status")

    @pytest.mark.asyncio
    async def test_full_reconciliation_flow_mocked(self, engine, blueprint):
        """Verify full reconcile flow with mocked success responses."""
        
        # Mock Responses for:
        # 1. Auth (Success)
        # 2. Get State (Empty -> implies creating)
        # 3. Clone (Success)
        # 4. Start (Success)
        
        # We use side_effect on request to return different responses based on arguments
        
        async def mock_request(method, url, **kwargs):
            # Normalize url check
            url_str = str(url)
            
            if "qemu" in url_str and method == "GET": 
                # get_state: return empty list
                return MagicMock(status_code=200, json=lambda: {"data": []})
                
            if "lxc" in url_str and method == "GET": 
                return MagicMock(status_code=200, json=lambda: {"data": []})
                
            if "clone" in url_str: 
                return MagicMock(status_code=200, json=lambda: {"data": "UPID:node:clone:1"})
                
            if "nextid" in url_str: 
                return MagicMock(status_code=200, json=lambda: {"data": "105"})
                
            if "tasks" in url_str: 
                # _wait_for_task
                return MagicMock(status_code=200, json=lambda: {"data": {"status": "stopped", "exitstatus": "OK"}})
                
            if "start" in url_str: 
                return MagicMock(status_code=200, json=lambda: {"data": "UPID:node:start:1"})
                
            # Default success
            return MagicMock(status_code=200, json=lambda: {"data": {}})

        # We need to mock _authenticate separately or ensure request handles it?
        # Let's mock _authenticate to be safe and focus on the reconcile flow logic
        with patch.object(engine, "_authenticate", return_value=True):
            engine.ticket = "mock"
            engine.csrf_token = "mock"
            
            # Mock _get_vm_by_name to return a fake template so cloning logic triggers
            # We mock _api_request for specific calls? No, we want to test the full flow including _api_request logic.
            # So we patch httpx.AsyncClient.request
            
            with patch("httpx.AsyncClient.request", side_effect=mock_request) as mock_req:
                
                # Also mock get_vm_by_name logic which uses _api_request
                # But wait, our mock_request handles "qemu" GET which returns [], so _get_vm_by_name("ubuntu") will fail returning None
                # We need it to return found for the template, but [] for the NEW vm.
                
                # Let's mock _get_vm_by_name explicitly to return template, 
                # AND ensure get_state calls work.
                
                # Wait, reconcile calls get_state which calls _api_request("GET", ...qemu)
                # apply calls _get_vm_by_name(template) which calls _api_request("GET", ...qemu)
                
                # So the mock_request needs to be smarter or we mock the higher level methods.
                # Since this is integration of the ENGINE logic (not just API wrapper), 
                # mocking _get_vm_by_name is acceptable to bypass detailed browsing logic.
                
                with patch.object(engine, "_get_vm_by_name") as mock_get_vm:
                    # First call (template check) -> returns dict
                    # Second call (check for update) -> returns dict?
                    
                    # Implementation detail: 
                    # get_state calls _api_request directly.
                    # apply calls _get_vm_by_name for template.
                    
                    mock_get_vm.return_value = {"vmid": 9000, "name": "ubuntu", "type": "qemu"}
                    
                    await engine.reconcile(blueprint)
                
                # Assertions
                # Verify Clone was called
                clones = [c for c in mock_req.call_args_list if "clone" in str(c)]
                assert len(clones) > 0

    @pytest.mark.asyncio
    async def test_server_error_500_resilience(self, engine):
        """Verify 500 errors are raised effectively."""
        mock_500 = MagicMock()
        mock_500.status_code = 500
        mock_500.raise_for_status.side_effect = httpx.HTTPStatusError("500 Error", request=MagicMock(), response=mock_500)
        
        with patch.object(engine, "_authenticate", return_value=True):
            engine.ticket = "mock"
            engine.csrf_token = "mock"

            with patch("httpx.AsyncClient.request", return_value=mock_500):
                # Engine should check status_code and raise
                with pytest.raises(httpx.HTTPStatusError):
                    await engine._api_request("GET", "cluster/status")
