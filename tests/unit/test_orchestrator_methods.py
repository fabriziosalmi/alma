"""Additional tests for EnhancedOrchestrator methods to boost coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from alma.core.llm_orchestrator import EnhancedOrchestrator


class TestEnhancedOrchestratorMethods:
    """Test EnhancedOrchestrator methods for coverage."""

    @pytest.fixture
    def orchestrator_no_llm(self):
        """Orchestrator without LLM."""
        return EnhancedOrchestrator(use_llm=False)

    @pytest.fixture
    def orchestrator_with_mock_llm(self):
        """Orchestrator with mock LLM."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock()
        mock_llm.function_call = AsyncMock()
        return EnhancedOrchestrator(llm=mock_llm, use_llm=True)

    async def test_execute_function_call_no_llm(self, orchestrator_no_llm):
        """Test function call without LLM returns error."""
        result = await orchestrator_no_llm.execute_function_call("test input")
        assert result["success"] is False
        assert "LLM not available" in result["error"]

    async def test_execute_function_call_invalid_response(self, orchestrator_with_mock_llm):
        """Test function call with invalid LLM response."""
        orchestrator_with_mock_llm.llm.function_call.return_value = None
        result = await orchestrator_with_mock_llm.execute_function_call("test input")
        assert result["success"] is False
        assert "did not return valid function call" in result["error"]

    async def test_execute_function_call_no_function_key(self, orchestrator_with_mock_llm):
        """Test function call without function key in response."""
        orchestrator_with_mock_llm.llm.function_call.return_value = {"arguments": {}}
        result = await orchestrator_with_mock_llm.execute_function_call("test input")
        assert result["success"] is False

    async def test_execute_function_call_exception(self, orchestrator_with_mock_llm):
        """Test function call exception handling."""
        orchestrator_with_mock_llm.llm.function_call.side_effect = Exception("Test error")
        result = await orchestrator_with_mock_llm.execute_function_call("test input")
        assert result["success"] is False
        assert "failed" in result["error"]

    def test_get_available_tools(self, orchestrator_no_llm):
        """Test getting available tools."""
        tools = orchestrator_no_llm.get_available_tools()
        assert isinstance(tools, list)

    async def test_parse_intent_with_llm_fallback(self, orchestrator_no_llm):
        """Test intent parsing without LLM falls back to rules."""
        result = await orchestrator_no_llm.parse_intent_with_llm("deploy kubernetes cluster")
        assert "intent" in result
        assert "confidence" in result

    async def test_parse_intent_with_llm_success(self, orchestrator_with_mock_llm):
        """Test intent parsing with LLM success."""
        orchestrator_with_mock_llm.llm.generate.return_value = (
            '{"intent": "deploy", "confidence": 0.9, "entities": {}}'
        )
        result = await orchestrator_with_mock_llm.parse_intent_with_llm("deploy cluster")
        assert result["intent"] == "deploy"
        assert result["confidence"] == 0.9

    async def test_parse_intent_with_llm_exception(self, orchestrator_with_mock_llm):
        """Test intent parsing with LLM exception falls back."""
        orchestrator_with_mock_llm.llm.generate.side_effect = Exception("LLM error")
        result = await orchestrator_with_mock_llm.parse_intent_with_llm("deploy cluster")
        # Should fallback to rule-based
        assert "intent" in result

    async def test_natural_language_to_blueprint_fallback(self, orchestrator_no_llm):
        """Test blueprint generation without LLM falls back."""
        result = await orchestrator_no_llm.natural_language_to_blueprint(
            "kubernetes cluster with nginx"
        )
        assert "version" in result
        assert "resources" in result

    async def test_natural_language_to_blueprint_with_llm(self, orchestrator_with_mock_llm):
        """Test blueprint generation with LLM."""
        orchestrator_with_mock_llm.llm.generate.return_value = """
```yaml
name: test-blueprint
resources:
  - type: service
```
"""
        result = await orchestrator_with_mock_llm.natural_language_to_blueprint("test")
        assert "resources" in result or "version" in result

    async def test_natural_language_to_blueprint_exception(self, orchestrator_with_mock_llm):
        """Test blueprint generation exception falls back."""
        orchestrator_with_mock_llm.llm.generate.side_effect = Exception("LLM error")
        result = await orchestrator_with_mock_llm.natural_language_to_blueprint("test")
        assert "version" in result

    async def test_blueprint_to_natural_language_fallback(self, orchestrator_no_llm):
        """Test blueprint description without LLM."""
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_no_llm.blueprint_to_natural_language(blueprint)
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_blueprint_to_natural_language_with_llm(self, orchestrator_with_mock_llm):
        """Test blueprint description with LLM."""
        orchestrator_with_mock_llm.llm.generate.return_value = "This is a test infrastructure"
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_with_mock_llm.blueprint_to_natural_language(blueprint)
        assert "test infrastructure" in result

    async def test_blueprint_to_natural_language_exception(self, orchestrator_with_mock_llm):
        """Test blueprint description exception."""
        orchestrator_with_mock_llm.llm.generate.side_effect = Exception("LLM error")
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_with_mock_llm.blueprint_to_natural_language(blueprint)
        assert isinstance(result, str)

    async def test_suggest_improvements_fallback(self, orchestrator_no_llm):
        """Test improvement suggestions without LLM."""
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_no_llm.suggest_improvements(blueprint)
        assert isinstance(result, list)

    async def test_suggest_improvements_with_llm(self, orchestrator_with_mock_llm):
        """Test improvement suggestions with LLM."""
        orchestrator_with_mock_llm.llm.generate.return_value = """
1. Add monitoring
2. Implement autoscaling
3. Use managed databases
"""
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_with_mock_llm.suggest_improvements(blueprint)
        assert isinstance(result, list)

    async def test_suggest_improvements_exception(self, orchestrator_with_mock_llm):
        """Test improvement suggestions exception."""
        orchestrator_with_mock_llm.llm.generate.side_effect = Exception("LLM error")
        blueprint = {"version": "1.0", "name": "test", "resources": []}
        result = await orchestrator_with_mock_llm.suggest_improvements(blueprint)
        assert isinstance(result, list)

    async def test_estimate_resources_no_llm(self, orchestrator_no_llm):
        """Test resource estimation without LLM."""
        result = await orchestrator_no_llm.estimate_resources("web", "high")
        assert "cpu" in result
        assert "memory" in result
        assert "reasoning" in result

    async def test_estimate_resources_with_llm(self, orchestrator_with_mock_llm):
        """Test resource estimation with LLM."""
        orchestrator_with_mock_llm.llm.generate.return_value = """
```json
{
    "cpu": 4,
    "memory": "8GB",
    "storage": "100GB",
    "reasoning": "High load web server"
}
```
"""
        result = await orchestrator_with_mock_llm.estimate_resources("web", "high")
        assert "cpu" in result or "memory" in result


class TestParseNumberedList:
    """Test _parse_numbered_list method."""

    @pytest.fixture
    def orchestrator(self):
        """Orchestrator fixture."""
        return EnhancedOrchestrator(use_llm=False)

    def test_parse_numbered_list_basic(self, orchestrator):
        """Test parsing simple numbered list."""
        text = """
1. First item
2. Second item
3. Third item
"""
        result = orchestrator._parse_numbered_list(text)
        assert len(result) == 3
        assert "First item" in result[0]
        assert "Second item" in result[1]
        assert "Third item" in result[2]

    def test_parse_numbered_list_with_prefix(self, orchestrator):
        """Test parsing numbered list with prefix text."""
        text = """
Here are some suggestions:

1. Add monitoring
2. Implement backups
3. Use CDN
"""
        result = orchestrator._parse_numbered_list(text)
        assert len(result) >= 2

    def test_parse_numbered_list_empty(self, orchestrator):
        """Test parsing empty text."""
        result = orchestrator._parse_numbered_list("")
        assert result == []

    def test_parse_numbered_list_no_numbers(self, orchestrator):
        """Test parsing text without numbers."""
        text = "Just some plain text without numbering"
        result = orchestrator._parse_numbered_list(text)
        assert result == []
