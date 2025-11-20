"""Tests for LLM service to boost coverage."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from alma.core import llm_service
from alma.core.llm_service import (
    _get_lock,
    get_llm,
    get_orchestrator,
    initialize_llm,
    is_llm_enabled,
    shutdown_llm,
    warmup_llm,
)


class TestLLMServiceGetLock:
    """Test _get_lock helper function."""

    def test_get_lock_creates_new_lock(self):
        """Test that _get_lock creates a new lock."""
        lock = _get_lock()
        assert isinstance(lock, asyncio.Lock)


class TestLLMServiceInitialize:
    """Test LLM initialization."""

    @pytest.fixture(autouse=True)
    def reset_global_state(self):
        """Reset global LLM state before each test."""
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None
        yield
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None

    @pytest.mark.skip(reason="Skipping - Qwen3LLM import doesn't exist in llm_service")
    @patch("alma.core.llm_service.settings")
    @patch("alma.core.llm_service.Qwen3LLM")
    async def test_initialize_llm_mock_fallback(self, mock_qwen_class, mock_settings):
        """Test LLM initialization falls back to MockLLM."""
        mock_settings.llm_model_name = "mock"
        mock_settings.llm_device = "cpu"
        mock_settings.llm_max_tokens = 1000

        # Make Qwen3LLM raise ImportError
        mock_qwen_class.side_effect = ImportError("No module")

        llm = await initialize_llm()
        assert llm is not None
        # Should be MockLLM
        assert "Mock" in llm.__class__.__name__

    async def test_get_llm_when_none(self):
        """Test get_llm initializes when instance is None."""
        llm_service._llm_instance = None

        with patch("alma.core.llm_service.initialize_llm", new_callable=AsyncMock) as mock_init:
            from alma.core.llm import MockLLM

            mock_init.return_value = MockLLM()

            llm = await get_llm()
            assert llm is not None
            mock_init.assert_called_once()

    async def test_get_llm_when_exists(self):
        """Test get_llm returns existing instance."""
        from alma.core.llm import MockLLM

        mock_llm = MockLLM()
        llm_service._llm_instance = mock_llm

        llm = await get_llm()
        assert llm is mock_llm


class TestGetOrchestrator:
    """Test orchestrator initialization."""

    @pytest.fixture(autouse=True)
    def reset_global_state(self):
        """Reset global state before each test."""
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None
        yield
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None

    async def test_get_orchestrator_with_real_llm(self):
        """Test getting orchestrator with real LLM flag."""
        from alma.core.llm import MockLLM

        with patch("alma.core.llm_service.get_llm", new_callable=AsyncMock) as mock_get_llm:
            mock_get_llm.return_value = MockLLM()

            orch = await get_orchestrator(use_real_llm=True)
            assert orch is not None
            mock_get_llm.assert_called_once()

    async def test_get_orchestrator_without_llm(self):
        """Test getting orchestrator without real LLM."""
        orch = await get_orchestrator(use_real_llm=False)
        assert orch is not None

    async def test_get_orchestrator_llm_error(self):
        """Test orchestrator creation when LLM fails."""
        with patch("alma.core.llm_service.get_llm", side_effect=Exception("LLM error")):
            orch = await get_orchestrator(use_real_llm=True)
            assert orch is not None

    async def test_get_orchestrator_returns_cached(self):
        """Test that orchestrator is cached."""
        from alma.core.llm_orchestrator import EnhancedOrchestrator

        orch1 = EnhancedOrchestrator(use_llm=False)
        llm_service._orchestrator_instance = orch1

        orch2 = await get_orchestrator()
        assert orch2 is orch1


class TestShutdownLLM:
    """Test LLM shutdown."""

    @pytest.fixture(autouse=True)
    def reset_global_state(self):
        """Reset global state before each test."""
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None
        yield
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None

    async def test_shutdown_llm_with_close_method(self):
        """Test shutdown when LLM has close method."""
        mock_llm = AsyncMock()
        mock_llm.close = AsyncMock()
        llm_service._llm_instance = mock_llm

        await shutdown_llm()

        mock_llm.close.assert_called_once()
        assert llm_service._llm_instance is None

    async def test_shutdown_llm_without_close_method(self):
        """Test shutdown when LLM has no close method."""
        from alma.core.llm import MockLLM

        llm_service._llm_instance = MockLLM()

        await shutdown_llm()

        assert llm_service._llm_instance is None

    async def test_shutdown_llm_with_orchestrator(self):
        """Test shutdown with orchestrator instance."""
        from alma.core.llm_orchestrator import EnhancedOrchestrator

        orch = EnhancedOrchestrator(use_llm=False)
        llm_service._orchestrator_instance = orch

        await shutdown_llm()

        assert llm_service._orchestrator_instance is None

    async def test_shutdown_llm_when_none(self):
        """Test shutdown when instances are None."""
        llm_service._llm_instance = None
        llm_service._orchestrator_instance = None

        # Should not raise
        await shutdown_llm()


class TestLLMConfiguration:
    """Test LLM configuration helpers."""

    @patch("alma.core.llm_service.settings")
    def test_is_llm_enabled_true(self, mock_settings):
        """Test is_llm_enabled returns True."""
        mock_settings.llm_model_name = "qwen3"
        mock_settings.llm_device = "cuda"

        assert is_llm_enabled() is True

    @patch("alma.core.llm_service.settings")
    def test_is_llm_enabled_false_mock_model(self, mock_settings):
        """Test is_llm_enabled returns False for mock model."""
        mock_settings.llm_model_name = "mock"
        mock_settings.llm_device = "cpu"

        assert is_llm_enabled() is False

    @patch("alma.core.llm_service.settings")
    def test_is_llm_enabled_false_no_device(self, mock_settings):
        """Test is_llm_enabled returns False for no device."""
        mock_settings.llm_model_name = "qwen3"
        mock_settings.llm_device = "none"

        assert is_llm_enabled() is False


class TestWarmupLLM:
    """Test LLM warmup."""

    @pytest.fixture(autouse=True)
    def reset_global_state(self):
        """Reset global state before each test."""
        llm_service._llm_instance = None
        yield
        llm_service._llm_instance = None

    async def test_warmup_llm_success(self):
        """Test successful LLM warmup."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value="Hello!")

        with patch("alma.core.llm_service.get_llm", new_callable=AsyncMock) as mock_get_llm:
            mock_get_llm.return_value = mock_llm

            await warmup_llm()

            mock_llm.generate.assert_called_once()
            call_args = mock_llm.generate.call_args
            assert "Hello" in call_args[0]

    async def test_warmup_llm_exception(self):
        """Test warmup handles exceptions."""
        with patch("alma.core.llm_service.get_llm", side_effect=Exception("Warmup error")):
            # Should not raise
            await warmup_llm()
