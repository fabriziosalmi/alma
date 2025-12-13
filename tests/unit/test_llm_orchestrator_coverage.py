"""Unit tests for EnhancedOrchestrator."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from alma.core.llm_orchestrator import EnhancedOrchestrator
from alma.core.llm import LLMInterface
from alma.core.tools import InfrastructureTools

@pytest.fixture
def mock_llm():
    return AsyncMock(spec=LLMInterface)

@pytest.fixture
def orchestrator(mock_llm):
    return EnhancedOrchestrator(llm=mock_llm)

class TestLLMOrchestratorParsing:
    def test_extract_json_valid(self, orchestrator):
        text = 'Some text {"key": "value"} end.'
        result = orchestrator._extract_json(text)
        assert result == {"key": "value"}

    def test_extract_json_fail(self, orchestrator):
        result = orchestrator._extract_json("No json here")
        assert result is None

    def test_extract_yaml_code_block(self, orchestrator):
        text = '```yaml\nkey: value\n```'
        result = orchestrator._extract_yaml(text)
        assert result == {"key": "value"}

    def test_extract_yaml_plain(self, orchestrator):
        text = 'key: value'
        result = orchestrator._extract_yaml(text)
        assert result == {"key": "value"}

    def test_parse_numbered_list(self, orchestrator):
        text = "1. Item 1\n2) Item 2\n3. Item 3"
        result = orchestrator._parse_numbered_list(text)
        assert result == ["Item 1", "Item 2", "Item 3"]

class TestLLMOrchestratorLogic:
    @pytest.mark.asyncio
    async def test_parse_intent_with_llm(self, orchestrator, mock_llm):
        """Test intent parsing."""
        mock_llm.generate.return_value = '{"intent": "create", "confidence": 0.9}'
        result = await orchestrator.parse_intent_with_llm("Create VM")
        assert result["intent"] == "create"
        assert result["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_estimate_resources_fallback(self, orchestrator, mock_llm):
        """Test fallback when LLM fails."""
        mock_llm.generate.side_effect = Exception("LLM Error")
        result = await orchestrator.estimate_resources("web", "high")
        assert result["cpu"] == 4
        assert result["reasoning"] == "Conservative default recommendations"

    @pytest.mark.asyncio
    async def test_execute_function_call_success(self, orchestrator, mock_llm):
        """Test function execution success via Native Tools."""
        # 1. LLM returns function call
        mock_llm.function_call.return_value = {
            "function": "create_vm",
            "arguments": {"name": "test"}
        }

        # 2. Mock execute_tool on the internal tools object
        # Ensure return_value is a MagicMock (not AsyncMock) so model_dump works synchronously
        mock_res = MagicMock()
        mock_res.model_dump.return_value = {"status": "success"}
        
        with patch.object(orchestrator.tools, "execute_tool", new=AsyncMock(return_value=mock_res)) as mock_exec:
            result = await orchestrator.execute_function_call("Create a VM named test")
            
            assert result["status"] == "success"
            mock_exec.assert_called_once()


    @pytest.mark.asyncio
    async def test_execute_function_call_mcp(self, orchestrator, mock_llm):
        """Test execution of MCP tool logic (mocking the internal import)."""
        mock_llm.function_call.return_value = {
            "function": "deploy_vm",
            "arguments": {"name": "mcp-vm", "template": "ubuntu"}
        }
        
        # Mock alma.mcp_server module
        mock_mcp = MagicMock()
        mock_deploy = AsyncMock(return_value='{"status": "mcp_success"}')
        mock_mcp.deploy_vm = mock_deploy
        
        with patch.dict("sys.modules", {"alma.mcp_server": mock_mcp}):
            result = await orchestrator.execute_function_call("Deploy VM")
            
            # The orchestrator parses the JSON string returned by MCP tool
            assert result["status"] == "mcp_success"
            mock_deploy.assert_called_with(name="mcp-vm", template="ubuntu")
