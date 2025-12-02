"""Unit tests for AnsibleEngine."""

from unittest.mock import MagicMock, patch
import pytest
from alma.core.state import Plan
from alma.engines.ansible import AnsibleEngine
from alma.schemas.blueprint import ResourceDefinition, SystemBlueprint

@pytest.fixture
def engine():
    return AnsibleEngine()

@pytest.fixture
def sample_blueprint():
    return SystemBlueprint(
        id=1,
        created_at="2025-11-20T12:00:00",
        updated_at="2025-11-20T12:00:00",
        version="1.0",
        name="test-ansible-blueprint",
        resources=[
            ResourceDefinition(
                type="configuration",
                name="test-playbook",
                provider="ansible",
                specs={
                    "playbook": "---\n- hosts: localhost\n  tasks:\n    - debug: msg='hello'"
                },
            )
        ],
    )

class TestAnsibleEngine:
    
    @patch("alma.engines.ansible.ansible_runner")
    async def test_health_check_success(self, mock_runner, engine):
        mock_result = MagicMock()
        mock_result.status = "successful"
        mock_runner.run.return_value = mock_result
        
        assert await engine.health_check()
        mock_runner.run.assert_called_with(
            private_data_dir=engine.data_dir,
            host_pattern="localhost",
            module="ping",
            quiet=True
        )

    @patch("alma.engines.ansible.ansible_runner")
    async def test_apply_create(self, mock_runner, engine, sample_blueprint):
        mock_result = MagicMock()
        mock_result.status = "successful"
        mock_runner.run.return_value = mock_result
        
        plan = Plan(to_create=sample_blueprint.resources)
        
        with patch("builtins.open", new_callable=MagicMock) as mock_open:
            await engine.apply(plan)
            
            # Verify playbook write
            mock_open.assert_called()
            
            # Verify runner call
            mock_runner.run.assert_called()
            call_args = mock_runner.run.call_args[1]
            assert call_args["inventory"] == engine.inventory
            assert "test-playbook.yml" in call_args["playbook"]

    @patch("alma.engines.ansible.ansible_runner")
    async def test_apply_failure(self, mock_runner, engine, sample_blueprint):
        mock_result = MagicMock()
        mock_result.status = "failed"
        mock_result.rc = 1
        mock_runner.run.return_value = mock_result
        
        plan = Plan(to_create=sample_blueprint.resources)
        
        with patch("builtins.open", new_callable=MagicMock):
            with pytest.raises(RuntimeError, match="Ansible playbook failed"):
                await engine.apply(plan)
