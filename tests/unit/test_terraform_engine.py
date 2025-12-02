"""Unit tests for TerraformEngine."""

import json
import os
from unittest.mock import MagicMock, patch
import pytest
from alma.core.state import Plan, ResourceState
from alma.engines.terraform import TerraformEngine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint

@pytest.fixture
def engine():
    return TerraformEngine(config={"work_dir": "/tmp/test-terraform"})

@pytest.fixture
def sample_blueprint():
    return SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        version="1.0",
        name="test-tf-blueprint",
        resources=[
            ResourceDefinition(
                type="terraform_stack",
                name="test-stack",
                provider="terraform",
                specs={
                    "hcl": 'resource "null_resource" "example" {}'
                },
            )
        ],
    )

class TestTerraformEngine:
    
    @patch("shutil.which")
    @patch("subprocess.Popen")
    async def test_health_check_success(self, mock_popen, mock_which, engine):
        mock_which.return_value = "/usr/bin/terraform"
        
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Terraform v1.0.0", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        assert await engine.health_check()
        mock_popen.assert_called()

    @patch("shutil.which")
    @patch("subprocess.Popen")
    async def test_apply_create(self, mock_popen, mock_which, engine, sample_blueprint):
        mock_which.return_value = "/usr/bin/terraform"
        
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        plan = Plan(to_create=sample_blueprint.resources)
        
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            with patch("os.makedirs"):
                await engine.apply(plan)
            
            # Verify HCL write
            mock_open.assert_called()
            
            # Verify init and apply calls
            assert mock_popen.call_count >= 2
            calls = mock_popen.call_args_list
            init_call = calls[-2]
            apply_call = calls[-1]
            
            assert "init" in init_call[0][0]
            assert "apply" in apply_call[0][0]

    @patch("shutil.which")
    @patch("subprocess.Popen")
    async def test_get_state(self, mock_popen, mock_which, engine, sample_blueprint):
        mock_which.return_value = "/usr/bin/terraform"
        
        state_json = {
            "values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "null_resource.example",
                            "values": {"id": "123"}
                        }
                    ]
                }
            }
        }
        
        process_mock = MagicMock()
        process_mock.communicate.return_value = (json.dumps(state_json), "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        with patch("os.path.exists", return_value=True):
            state = await engine.get_state(sample_blueprint)
            
        assert len(state) == 1
        assert state[0].id == "null_resource.example"

    @patch("shutil.which")
    @patch("subprocess.Popen")
    async def test_destroy(self, mock_popen, mock_which, engine):
        mock_which.return_value = "/usr/bin/terraform"
        
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock
        
        resource_state = ResourceState(id="test-stack", type="terraform_stack", config={})
        plan = Plan(to_delete=[resource_state])
        
        with patch("os.path.exists", return_value=True):
            with patch("shutil.rmtree") as mock_rmtree:
                await engine.destroy(plan)
                mock_rmtree.assert_called()
        
        # Verify destroy call
        args = mock_popen.call_args[0][0]
        assert "destroy" in args
