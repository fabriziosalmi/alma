"""LLM service initialization and management."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from alma.core.config import get_settings
from alma.core.llm import LLMInterface, MockLLM
from alma.core.llm_orchestrator import EnhancedOrchestrator


# --- Local Studio LLM Implementation (Tier 2) ---
class LocalStudioLLM(LLMInterface):
    """
    Tier 2: Local Mesh.
    Connects to a local LLM instance (e.g., LM Studio) via HTTP.
    Provides a resilient fallback when the cloud is unreachable.
    """

    def __init__(self, base_url: str, model_name: str):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = 30.0  # Longer timeout for generation

        # Resilience
        from alma.core.resilience import CircuitBreaker, Retrier

        self.circuit_breaker = CircuitBreaker(name="LocalStudioLLM")
        self.retrier = Retrier(max_attempts=3, base_delay=1.0)

    async def _initialize(self) -> None:
        """
        Checks connectivity to the local LLM service.
        """
        print(f"  -> Pinging Local Studio at {self.base_url}...")
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if the server is responsive.
            # For LM Studio, a GET to /v1/models confirms availability.
            models_url = self.base_url.replace("/chat/completions", "/models")
            resp = await client.get(models_url)
            resp.raise_for_status()
            print("  -> Local Studio is ONLINE.")

    async def generate(
        self, prompt: str, context: dict[str, Any] | None = None, schema: dict[str, Any] | None = None, **kwargs: Any
    ) -> str:
        """
        Generates text using the local LLM.
        """
        messages = [{"role": "user", "content": prompt}]
        if context:
            # Prepend context as system message or context
            system_msg = f"Context: {context}"
            messages.insert(0, {"role": "system", "content": system_msg})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": settings.llm_max_tokens,
            "stream": False,
        }

        # Enhanced Feature: Structured Output / Schema Enforcement
        if schema:
            # If supported (LM Studio / OpenAI-compatible with strict logic)
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "strict_response",
                    "strict": True,
                    "schema": schema
                }
            }
            # Fallback/Safety: Instructions are key even with strict mode
            # But here we relay on the API. Could also inject into prompt as backup.

        async def _request() -> str:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.base_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return str(data["choices"][0]["message"]["content"])

        try:
            # Wrap request with Retrier -> CircuitBreaker -> Request
            return await self.retrier.call(lambda: self.circuit_breaker.call(_request))
        except Exception as e:
            print(f"Error generating with LocalStudioLLM: {e}")
            raise  # Re-raise to trigger fallback to Tier 3

    async def function_call(
        self, prompt: str, tools: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Basic function calling support for Local Studio.
        """
        # Note: Full function calling support depends on the local model's capabilities.
        # For now, we treat it as a generation request.
        content = await self.generate(prompt, context)
        return {"content": content}

    async def close(self) -> None:
        pass


# --- TinyLLM Implementation (Tier 3 - Panic) ---
class TinyLLM(LLMInterface):
    """
    Tier 3: Panic Mode.
    A minimal, local-only LLM fallback.
    Uses simple heuristics or a tiny local model (e.g., quantized) if available.
    For now, it provides safe, canned responses to keep the system alive.
    """

    def __init__(self) -> None:
        self.model_name = "tiny-llm-fallback"

    async def _initialize(self) -> None:
        pass

    async def generate(
        self, prompt: str, context: dict[str, Any] | None = None, schema: dict[str, Any] | None = None, **kwargs: Any
    ) -> str:
        """
        Generates a safe, minimal response.
        """
        # Simple heuristic response
        return (
            "I am currently operating in Offline Mode (TinyLLM). "
            "I can acknowledge your request, but advanced cognitive functions are temporarily unavailable. "
            "Please check your connection or try again later."
        )

    async def function_call(
        self, prompt: str, tools: list[dict[str, Any]], context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Mock function call for TinyLLM.
        """
        return {"content": self.generate(prompt)}

    async def close(self) -> None:
        pass


settings = get_settings()

# Global instances
_llm_instance: LLMInterface | None = None
_orchestrator_instance: EnhancedOrchestrator | None = None
_initialization_lock: asyncio.Lock | None = None


def _get_lock() -> asyncio.Lock:
    """Get or create the initialization lock for the current event loop."""
    global _initialization_lock
    try:
        # Check if lock exists and belongs to current loop
        # Note: _loop is internal, but we need to ensure thread safety across event loops if using multiple
        # Checking existence is sufficient for single-threaded async contexts.
        if _initialization_lock is None:
            _initialization_lock = asyncio.Lock()
    except RuntimeError:
        # No event loop running
        _initialization_lock = asyncio.Lock()
    return _initialization_lock


async def initialize_llm() -> LLMInterface:
    """
    Initialize LLM instance with 3-Tier Fallback (Resiliency Policy).

    Priority 1: Cloud (Qwen3 via API/Transformers)
    Priority 2: Local Mesh (LocalStudioLLM via localhost:1234)
    Priority 3: Panic (TinyLLM static fallback)

    Returns:
        LLM interface instance
    """
    global _llm_instance

    async with _get_lock():
        if _llm_instance is not None:
            return _llm_instance

        # --- Tier 1: Cloud / Primary ---
        try:
            print(f"Attempting Tier 1 (Cloud): {settings.llm_model_name}...")
            # Try to import and initialize Qwen3
            from alma.core.llm_qwen import Qwen3LLM

            # Check if we are configured for a real model
            if settings.llm_model_name == "mock":
                raise ImportError("Mock mode configured")

            cloud_instance = Qwen3LLM(
                model_name=settings.llm_model_name,
                device=settings.llm_device,
                max_tokens=settings.llm_max_tokens,
            )
            await cloud_instance._initialize()
            _llm_instance = cloud_instance
            print("✓ Tier 1 (Cloud) initialized successfully")
            return _llm_instance

        except Exception as e:
            print(f"⚠ Tier 1 (Cloud) failed: {e}")

        # --- Tier 2: Local Mesh ---
        try:
            print(
                f"Attempting Tier 2 (Local Mesh): {settings.llm_local_studio_model} at {settings.llm_local_studio_url}..."
            )
            local_instance = LocalStudioLLM(
                base_url=settings.llm_local_studio_url, model_name=settings.llm_local_studio_model
            )
            await local_instance._initialize()
            _llm_instance = local_instance
            print("✓ Tier 2 (Local Mesh) initialized successfully")
            return _llm_instance

        except Exception as e:
            print(f"⚠ Tier 2 (Local Mesh) failed: {e}")

        # --- Tier 3: Panic ---
        print("Attempting Tier 3 (Panic): TinyLLM...")
        _llm_instance = TinyLLM()
        print("✓ Tier 3 (Panic) initialized (Offline Mode)")

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
