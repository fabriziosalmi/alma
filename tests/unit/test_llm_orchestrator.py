"""Unit tests for Enhanced LLM Orchestrator."""


import pytest

from alma.core.llm import MockLLM
from alma.core.llm_orchestrator import EnhancedOrchestrator


@pytest.fixture
def mock_llm():
    """Create MockLLM instance."""
    return MockLLM()


@pytest.fixture
def orchestrator_with_llm(mock_llm):
    """Create EnhancedOrchestrator with MockLLM."""
    return EnhancedOrchestrator(llm=mock_llm, use_llm=True)


@pytest.fixture
def orchestrator_without_llm():
    """Create EnhancedOrchestrator without LLM (rule-based)."""
    return EnhancedOrchestrator(llm=None, use_llm=False)


class TestEnhancedOrchestrator:
    """Tests for EnhancedOrchestrator class."""

    def test_initialization_with_llm(self, mock_llm):
        """Test orchestrator initialization with LLM."""
        orch = EnhancedOrchestrator(llm=mock_llm, use_llm=True)
        assert orch.llm is not None
        assert orch.use_llm is True

    def test_initialization_without_llm(self):
        """Test orchestrator initialization without LLM."""
        orch = EnhancedOrchestrator(llm=None, use_llm=False)
        assert orch.use_llm is False

    async def test_parse_intent_fallback_to_rules(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test intent parsing fallback to rules when LLM disabled."""
        intent = await orchestrator_without_llm.parse_intent_with_llm("Create a web server")

        assert intent["intent"] == "create_blueprint"
        assert "raw_input" in intent

    async def test_blueprint_generation_fallback(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test blueprint generation fallback to rules."""
        blueprint = await orchestrator_without_llm.natural_language_to_blueprint(
            "I need a web server and database"
        )

        assert "version" in blueprint
        assert "resources" in blueprint
        assert len(blueprint["resources"]) >= 2  # web + db

    async def test_description_generation_fallback(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test description generation fallback."""
        blueprint = {
            "name": "test-app",
            "resources": [
                {
                    "type": "compute",
                    "name": "web-server",
                    "specs": {"cpu": 2, "memory": "4GB"},
                }
            ],
        }

        description = await orchestrator_without_llm.blueprint_to_natural_language(blueprint)

        assert "test-app" in description
        assert "web-server" in description

    async def test_improvements_fallback(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test improvement suggestions fallback."""
        blueprint = {
            "name": "single-server",
            "resources": [
                {
                    "type": "compute",
                    "name": "server",
                    "specs": {"cpu": 1, "memory": "512MB"},
                    "metadata": {},
                }
            ],
        }

        suggestions = await orchestrator_without_llm.suggest_improvements(blueprint)

        assert len(suggestions) > 0
        assert isinstance(suggestions, list)

    async def test_resource_sizing_with_llm(
        self, orchestrator_with_llm: EnhancedOrchestrator
    ) -> None:
        """Test resource sizing with LLM."""
        sizing = await orchestrator_with_llm.estimate_resources(
            "web application", "1000 users/hour"
        )

        assert "cpu" in sizing
        assert "memory" in sizing
        assert "reasoning" in sizing

    async def test_resource_sizing_without_llm(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test resource sizing without LLM."""
        sizing = await orchestrator_without_llm.estimate_resources(
            "web application", "1000 users/hour"
        )

        assert "cpu" in sizing
        assert "memory" in sizing
        assert sizing["cpu"] >= 2

    async def test_security_audit_without_llm(
        self, orchestrator_without_llm: EnhancedOrchestrator
    ) -> None:
        """Test security audit without LLM."""
        blueprint = {
            "name": "test",
            "resources": [{"type": "compute", "name": "server"}],
        }

        findings = await orchestrator_without_llm.security_audit(blueprint)

        assert len(findings) > 0
        assert "severity" in findings[0]

    def test_extract_json_valid(self, orchestrator_with_llm: EnhancedOrchestrator) -> None:
        """Test JSON extraction from text."""
        text = 'Some text {"key": "value", "number": 42} more text'
        result = orchestrator_with_llm._extract_json(text)

        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42

    def test_extract_json_invalid(self, orchestrator_with_llm: EnhancedOrchestrator) -> None:
        """Test JSON extraction with invalid JSON."""
        text = "No JSON here at all"
        result = orchestrator_with_llm._extract_json(text)

        assert result is None

    def test_extract_yaml_from_code_block(
        self, orchestrator_with_llm: EnhancedOrchestrator
    ) -> None:
        """Test YAML extraction from code block."""
        text = """
Here is the blueprint:
```yaml
version: "1.0"
name: test
resources: []
```
"""
        result = orchestrator_with_llm._extract_yaml(text)

        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "test"

    def test_extract_yaml_plain(self, orchestrator_with_llm: EnhancedOrchestrator) -> None:
        """Test YAML extraction from plain text."""
        text = """
version: "1.0"
name: test-blueprint
resources: []
"""
        result = orchestrator_with_llm._extract_yaml(text)

        assert result is not None
        assert result["version"] == "1.0"

    def test_parse_numbered_list(self, orchestrator_with_llm: EnhancedOrchestrator) -> None:
        """Test numbered list parsing."""
        text = """
1. First suggestion
2. Second suggestion
3. Third suggestion
Some other text
4) Fourth suggestion with parenthesis
"""
        items = orchestrator_with_llm._parse_numbered_list(text)

        assert len(items) >= 3
        assert "First suggestion" in items
        assert "Second suggestion" in items
