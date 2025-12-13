"""Unit tests for Proxmox State Reconciliation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from alma.engines.proxmox import ProxmoxEngine
from alma.core.state import Plan, ResourceState
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition

@pytest.fixture
def mock_engine():
    """Create a mocked ProxmoxEngine."""
    engine = ProxmoxEngine(config={"node": "test-node", "url": "https://pve:8006", "token": "a:b"})
    engine._authenticate = AsyncMock(return_value=True)
    engine._api_request = AsyncMock()
    return engine

@pytest.fixture
def sample_blueprint():
    """Create a simple blueprint."""
    from datetime import datetime
    return SystemBlueprint(
        id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="test-sys",
        resources=[
            ResourceDefinition(
                name="web-vm", 
                type="compute", 
                provider="proxmox", 
                specs={"cpu": 4, "memory": 4096, "template": "ubuntu"}
            ),
        ]
    )

class TestProxmoxReconciliation:

    @pytest.mark.asyncio
    async def test_get_state_normalization(self, mock_engine, sample_blueprint):
        """Test that get_state converts Proxmox units to ALMA specs."""
        
        # Mock Proxmox API return (Bytes for memory)
        mock_engine._api_request.side_effect = [
            [{"name": "web-vm", "status": "running", "maxmem": 4294967296, "maxcpu": 4}], # QEMU
            [] # LXC
        ]
        
        states = await mock_engine.get_state(sample_blueprint)
        
        assert len(states) == 1
        res = states[0]
        assert res.id == "web-vm"
        # 4294967296 bytes = 4096 MB
        assert res.config["memory"] == 4096 
        assert res.config["cpu"] == 4

    @pytest.mark.asyncio
    async def test_reconcile_no_drift(self, mock_engine, sample_blueprint):
        """Test reconciliation when state matches blueprint."""
        
        # Current state matches desired
        mock_engine.get_state = AsyncMock(return_value=[
            ResourceState(
                id="web-vm", 
                type="compute", 
                config={"cpu": 4, "memory": 4096, "template": "ubuntu"}
            )
        ])
        
        with patch("alma.engines.proxmox.diff_states") as mock_diff:
            mock_diff.return_value = Plan() # Empty plan
            
            await mock_engine.reconcile(sample_blueprint)
            
            # Should NOT call apply
            mock_engine.apply = AsyncMock()
            await mock_engine.reconcile(sample_blueprint)
            mock_engine.apply.assert_not_called()

    @pytest.mark.asyncio
    async def test_reconcile_with_drift_update(self, mock_engine, sample_blueprint):
        """Test reconciliation correcting configuration drift."""
        
        # Current state has LESS memory than desired (2GB vs 4GB)
        current_res = ResourceState(
            id="web-vm", 
            type="compute", 
            config={"cpu": 4, "memory": 2048} # DRIFT
        )
        mock_engine.get_state = AsyncMock(return_value=[current_res])
        
        # We need to simulate the apply process
        mock_engine.apply = AsyncMock()
        
        await mock_engine.reconcile(sample_blueprint)
        
        # Check that apply was called
        mock_engine.apply.assert_called_once()
        plan = mock_engine.apply.call_args[0][0]
        
        # Verify Plan content
        assert len(plan.to_update) == 1
        assert plan.to_update[0][0].id == "web-vm" # Current
        assert plan.to_update[0][1].name == "web-vm" # Desired

    @pytest.mark.asyncio
    async def test_reconcile_with_drift_missing(self, mock_engine, sample_blueprint):
        """Test reconciliation recreating missing resource."""
        
        # Current state is empty (VM deleted)
        mock_engine.get_state = AsyncMock(return_value=[])
        
        mock_engine.apply = AsyncMock()
        
        await mock_engine.reconcile(sample_blueprint)
        
        mock_engine.apply.assert_called_once()
        plan = mock_engine.apply.call_args[0][0]
        
        assert len(plan.to_create) == 1
        assert plan.to_create[0].name == "web-vm"
