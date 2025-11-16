"""Unit tests for Qwen3 LLM implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ai_cdn.core.llm_qwen import Qwen3LLM


@pytest.fixture
def qwen_llm():
    """Create Qwen3LLM instance (not initialized)."""
    return Qwen3LLM(model_name="Qwen/Qwen2.5-0.5B-Instruct", device="cpu")


class TestQwen3LLM:
    """Tests for Qwen3LLM class."""

    def test_initialization(self, qwen_llm: Qwen3LLM) -> None:
        """Test LLM initialization."""
        assert qwen_llm.model_name == "Qwen/Qwen2.5-0.5B-Instruct"
        assert qwen_llm.device == "cpu"
        assert not qwen_llm._initialized
        assert qwen_llm.model is None
        assert qwen_llm.tokenizer is None

    def test_device_selection_cpu(self) -> None:
        """Test CPU device selection."""
        llm = Qwen3LLM(device="cpu")
        assert llm.device == "cpu"

    def test_device_selection_auto_cpu(self) -> None:
        """Test automatic device selection (CPU fallback)."""
        with patch("torch.cuda.is_available", return_value=False):
            with patch("torch.backends.mps.is_available", return_value=False):
                llm = Qwen3LLM()
                assert llm.device == "cpu"

    def test_system_prompt(self, qwen_llm: Qwen3LLM) -> None:
        """Test system prompt generation."""
        prompt = qwen_llm._get_system_prompt()
        assert "infrastructure" in prompt.lower()
        assert "assistant" in prompt.lower()

    def test_format_functions(self, qwen_llm: Qwen3LLM) -> None:
        """Test function formatting."""
        functions = [
            {
                "name": "deploy_server",
                "description": "Deploy a server",
                "parameters": {"name": "str", "cpu": "int"},
            },
            {
                "name": "list_servers",
                "description": "List all servers",
                "parameters": {},
            },
        ]

        formatted = qwen_llm._format_functions(functions)

        assert "deploy_server" in formatted
        assert "Deploy a server" in formatted
        assert "list_servers" in formatted

    async def test_close(self, qwen_llm: Qwen3LLM) -> None:
        """Test resource cleanup."""
        # Mock initialized state
        qwen_llm._initialized = True
        qwen_llm.model = MagicMock()
        qwen_llm.tokenizer = MagicMock()

        await qwen_llm.close()

        assert qwen_llm.model is None
        assert qwen_llm.tokenizer is None
        assert not qwen_llm._initialized

    @pytest.mark.skipif(
        True,
        reason="Skipping actual model tests - requires downloading model",
    )
    async def test_generate_real_model(self) -> None:
        """Test generation with real model (integration test)."""
        llm = Qwen3LLM(model_name="Qwen/Qwen2.5-0.5B-Instruct", device="cpu")
        response = await llm.generate("Hello, how are you?")
        assert isinstance(response, str)
        assert len(response) > 0
        await llm.close()

    @pytest.mark.skipif(
        True,
        reason="Skipping actual model tests - requires downloading model",
    )
    async def test_function_call_real_model(self) -> None:
        """Test function calling with real model (integration test)."""
        llm = Qwen3LLM(model_name="Qwen/Qwen2.5-0.5B-Instruct", device="cpu")

        functions = [
            {
                "name": "create_server",
                "description": "Create a new server",
                "parameters": {"name": "str", "cpu": "int"},
            }
        ]

        result = await llm.function_call("Create a server named web-01 with 4 CPUs", functions)

        assert isinstance(result, dict)
        assert "function" in result or len(result) == 0
        await llm.close()
