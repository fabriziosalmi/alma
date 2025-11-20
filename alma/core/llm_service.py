"""LLM service initialization and management."""

from typing import Optional
import asyncio

from alma.core.llm import LLMInterface, MockLLM
from alma.core.llm_orchestrator import EnhancedOrchestrator
from alma.core.config import get_settings

settings = get_settings()

# Global instances
_llm_instance: Optional[LLMInterface] = None
_orchestrator_instance: Optional[EnhancedOrchestrator] = None
_initialization_lock: Optional[asyncio.Lock] = None


def _get_lock() -> asyncio.Lock:
    """Get or create the initialization lock for the current event loop."""
    global _initialization_lock
    try:
        if _initialization_lock is None or _initialization_lock._loop != asyncio.get_event_loop():
            _initialization_lock = asyncio.Lock()
    except RuntimeError:
        # No event loop running
        _initialization_lock = asyncio.Lock()
    return _initialization_lock


async def initialize_llm() -> LLMInterface:
    """
    Initialize LLM instance.

    Returns:
        LLM interface instance
    """
    global _llm_instance

    async with _get_lock():
        if _llm_instance is not None:
            return _llm_instance

        try:
            # Try to import and initialize Qwen3
            from alma.core.llm_qwen import Qwen3LLM

            print(f"Initializing Qwen3 LLM: {settings.llm_model_name}")
            print(f"Device: {settings.llm_device}")

            _llm_instance = Qwen3LLM(
                model_name=settings.llm_model_name,
                device=settings.llm_device,
                max_tokens=settings.llm_max_tokens,
            )

            # Initialize the model
            await _llm_instance._initialize()

            print("✓ LLM initialized successfully")

        except ImportError as e:
            print(f"⚠ Could not load Qwen3 LLM: {e}")
            print("Falling back to MockLLM")
            _llm_instance = MockLLM()

        except Exception as e:
            print(f"⚠ LLM initialization failed: {e}")
            print("Falling back to MockLLM")
            _llm_instance = MockLLM()

        return _llm_instance


async def get_llm() -> LLMInterface:
    """
    Get LLM instance (initialize if needed).

    Returns:
        LLM interface instance
    """
    if _llm_instance is None:
        return await initialize_llm()
    return _llm_instance


async def get_orchestrator(use_real_llm: bool = True) -> EnhancedOrchestrator:
    """
    Get conversational orchestrator instance.

    Args:
        use_real_llm: Whether to use real LLM or fallback to rules

    Returns:
        EnhancedOrchestrator instance
    """
    global _orchestrator_instance

    async with _get_lock():
        if _orchestrator_instance is not None:
            return _orchestrator_instance

        llm = None
        if use_real_llm:
            try:
                llm = await get_llm()
            except Exception as e:
                print(f"Failed to get LLM for orchestrator: {e}")
                llm = MockLLM()

        _orchestrator_instance = EnhancedOrchestrator(llm=llm, use_llm=use_real_llm)

        return _orchestrator_instance


async def shutdown_llm() -> None:
    """Shutdown LLM and free resources."""
    global _llm_instance, _orchestrator_instance

    if _llm_instance is not None:
        if hasattr(_llm_instance, "close"):
            await _llm_instance.close()
        _llm_instance = None

    if _orchestrator_instance is not None:
        _orchestrator_instance.clear_history()
        _orchestrator_instance = None

    print("✓ LLM resources freed")


# Configuration helpers
def is_llm_enabled() -> bool:
    """
    Check if real LLM is enabled.

    Returns:
        True if LLM should be used
    """
    return settings.llm_model_name != "mock" and settings.llm_device != "none"


async def warmup_llm() -> None:
    """
    Warmup LLM with a simple query.

    This helps reduce latency for the first actual user request.
    """
    try:
        llm = await get_llm()
        print("Warming up LLM...")

        # Simple warmup query
        await llm.generate("Hello", context={"warmup": True})

        print("✓ LLM warmed up")

    except Exception as e:
        print(f"LLM warmup failed: {e}")
