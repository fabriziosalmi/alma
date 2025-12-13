"""Unit tests for Terraform Engine."""

import pytest
import subprocess
from unittest.mock import MagicMock, AsyncMock, patch
from alma.engines.terraform import TerraformEngine
from alma.schemas.blueprint import SystemBlueprint, ResourceDefinition
from datetime import datetime

@pytest.fixture
def engine():
    return TerraformEngine(config={"working_dir": "/tmp/tf"})

@pytest.fixture
def blueprint():
    return SystemBlueprint(
        id=1,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="test-tf-sys",
        resources=[
            ResourceDefinition(
                name="main-server",
                type="compute",
                provider="terraform",
                specs={"instance_type": "t2.micro"}
            )
        ]
    )

class TestTerraformEngine:

    @pytest.mark.asyncio
    async def test_health_check_success(self, engine):
        """Test health check passes with valid version output."""
        with patch("shutil.which", return_value="/usr/bin/terraform"), \
             patch.object(engine, "_run_command", return_value=(0, "Terraform v1.0.0", "")) as mock_run:
            assert await engine.health_check() is True
            mock_run.assert_called_with(["version"], cwd=".")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, engine):
        """Test health check fails on command error."""
        with patch("shutil.which", return_value="/usr/bin/terraform"), \
             patch.object(engine, "_run_command", return_value=(1, "", "Error")) as mock_run:
            assert await engine.health_check() is False

    @pytest.mark.asyncio
    async def test_apply_success(self, engine):
        """Test apply sequence: init -> apply."""
        
        resource = ResourceDefinition(
            name="main-server",
            type="compute",
            provider="terraform",
            specs={
                "instance_type": "t2.micro",
                "hcl": 'resource "aws_instance" "app" {}'
            }
        )
        plan = MagicMock()
        plan.to_create = [resource]
        plan.to_update = []
        
        # Mock run command to always succeed
        # Mock open/write for HCL file creation
        with patch("shutil.which", return_value="/usr/bin/terraform"), \
             patch("builtins.open", MagicMock()), \
             patch("os.makedirs"), \
             patch.object(engine, "_run_command", return_value=(0, "Success", "")) as mock_run:
            
            await engine.apply(plan)
            
            # Verify Calls:
            # 1. Init
            # 2. Apply
            
            calls = mock_run.call_args_list
            assert len(calls) >= 2
            assert calls[0][0][0] == ["init", "-no-color"]
            assert "apply" in calls[1][0][0]

    @pytest.mark.asyncio
    async def test_destroy_success(self, engine):
        # Need to simulate existence of directory so it doesn't skip
        with patch("shutil.which", return_value="/usr/bin/terraform"), \
             patch("os.path.exists", return_value=True), \
             patch("shutil.rmtree"), \
             patch.object(engine, "_run_command", return_value=(0, "Destruction complete", "")) as mock_run:
            
            res = MagicMock()
            res.id = "stack-id"
            plan = MagicMock()
            plan.to_delete = [res]
            
            await engine.destroy(plan)
            mock_run.assert_called()
            assert "destroy" in mock_run.call_args[0][0]

    @pytest.mark.asyncio
    async def test_run_command_impl(self, engine):
        """Test the subprocess wrapper directly."""
        # We need to mock subprocess.Popen
        with patch("subprocess.Popen") as mock_popen:
            process_mock = MagicMock()
            process_mock.communicate.return_value = ("stdout", "stderr")
            process_mock.returncode = 0
            mock_popen.return_value = process_mock
            
            code, out, err = engine._run_command(["test"], cwd="/tmp")
            
            assert code == 0
            assert out == "stdout"
            assert err == "stderr"
            mock_popen.assert_called_with(
                ["terraform", "test"], 
                cwd="/tmp", 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
