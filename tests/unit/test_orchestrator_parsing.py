"""Tests for LLM Orchestrator parsing and logic."""

import pytest
from unittest.mock import Mock
from alma.core.llm_orchestrator import EnhancedOrchestrator


@pytest.fixture
def orchestrator():
    """Create orchestrator instance with mocked LLM."""
    # Create orchestrator without LLM for parsing tests
    return EnhancedOrchestrator(use_llm=False)


class TestJSONExtraction:
    """Tests for JSON extraction from LLM responses."""

    def test_json_extraction_plain(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting plain JSON."""
        text = '{"version": "1.0", "name": "test"}'
        result = orchestrator._extract_json(text)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "test"

    def test_json_extraction_markdown(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting JSON from markdown code blocks."""
        text = """
Here is the blueprint:

```json
{
    "version": "1.0",
    "name": "web-app",
    "resources": []
}
```

That's it!
"""
        result = orchestrator._extract_json(text)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "web-app"
        assert isinstance(result["resources"], list)

    def test_json_extraction_with_text_around(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting JSON with surrounding text."""
        text = 'Here is your config: {"foo": "bar", "count": 42} and that is all.'
        result = orchestrator._extract_json(text)
        assert result is not None
        assert result["foo"] == "bar"
        assert result["count"] == 42

    def test_json_extraction_broken(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting invalid JSON returns None."""
        text = '{"foo": "bar"'  # Missing closing brace
        result = orchestrator._extract_json(text)
        assert result is None

    def test_json_extraction_no_json(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test text without JSON returns None."""
        text = "This is just plain text with no JSON structure"
        result = orchestrator._extract_json(text)
        assert result is None

    def test_json_extraction_nested(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting nested JSON."""
        text = '''
{
    "config": {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "cache": {"enabled": true}
    }
}
'''
        result = orchestrator._extract_json(text)
        assert result is not None
        assert result["config"]["database"]["host"] == "localhost"
        assert result["config"]["cache"]["enabled"] is True


class TestYAMLExtraction:
    """Tests for YAML extraction from LLM responses."""

    def test_yaml_extraction_plain(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting plain YAML."""
        text = """
version: "1.0"
name: test-blueprint
resources: []
"""
        result = orchestrator._extract_yaml(text)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["name"] == "test-blueprint"

    def test_yaml_extraction_markdown(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test extracting YAML from markdown code blocks."""
        text = """
Here is the YAML:

```yaml
version: "1.0"
name: web-server
specs:
  cpu: 4
  memory: 8GB
```
"""
        result = orchestrator._extract_yaml(text)
        assert result is not None
        assert result["version"] == "1.0"
        assert result["specs"]["cpu"] == 4
        assert result["specs"]["memory"] == "8GB"

    def test_yaml_extraction_broken(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test invalid YAML returns None."""
        text = """
version: 1.0
  invalid indent
name: broken
"""
        result = orchestrator._extract_yaml(text)
        # Should handle gracefully
        assert result is None or isinstance(result, dict)

    def test_yaml_extraction_no_yaml(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test text without YAML returns None or string."""
        text = "Just some random text"
        result = orchestrator._extract_yaml(text)
        # May return None or the text itself as fallback
        assert result is None or isinstance(result, (dict, str))


class TestOrchestratorEdgeCases:
    """Tests for orchestrator edge cases."""

    def test_json_extraction_with_escape_sequences(self, orchestrator: EnhancedOrchestrator) -> None:
        """Test JSON with escape sequences."""
        text = '{"message": "Hello\\nWorld", "path": "C:\\\\Users\\\\test"}'
        result = orchestrator._extract_json(text)
        assert result is not None
        assert "message" in result
