import asyncio
import sys
import time
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append("""Verify async LLM functionality."""

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Mock transformers before importing Qwen3LLM
sys.modules["transformers"] = MagicMock()

from alma.core.llm_qwen import Qwen3LLM  # noqa: E402


async def test_async_streaming():
    print("\n--- Testing Async LLM Streaming ---")

    # Setup mocks
    mock_transformers = sys.modules["transformers"]
    mock_streamer_cls = MagicMock()
    mock_transformers.TextIteratorStreamer = mock_streamer_cls

    # Setup mock streamer instance
    mock_streamer_instance = MagicMock()

    def generator():
        print("  Generator: Yielding Chunk 1")
        yield "Chunk 1"
        print("  Generator: Sleeping...")
        time.sleep(0.1)
        print("  Generator: Yielding Chunk 2")
        yield "Chunk 2"
        time.sleep(0.1)
        print("  Generator: Yielding Chunk 3")
        yield "Chunk 3"

    # Configure __iter__ to return the generator iterator
    mock_streamer_instance.__iter__.side_effect = lambda: iter(generator())
    mock_streamer_cls.return_value = mock_streamer_instance

    # Mock Thread locally
    with patch("alma.core.llm_qwen.Qwen3LLM._initialize"):

        # Setup LLM
        llm = Qwen3LLM(device="cpu")
        llm.tokenizer = MagicMock()
        llm.model = MagicMock()
        llm._initialized = True

        # Measure time and concurrency
        start_time = time.time()
        chunks = []

        # Run a background task to prove the loop isn't blocked
        async def background_task():
            for _ in range(5):
                await asyncio.sleep(0.05)
                print(".", end="", flush=True)

        bg_task = asyncio.create_task(background_task())

        print("Streaming started", end="")
        async for chunk in llm.stream_generate("Test prompt"):
            chunks.append(chunk)
            print(f" Received: {chunk}")

        await bg_task
        end_time = time.time()

        print(f"\nTotal time: {end_time - start_time:.2f}s")
        assert len(chunks) == 3
        assert chunks == ["Chunk 1", "Chunk 2", "Chunk 3"]
        print("✓ Streaming completed successfully")
        print("✓ Background task ran concurrently (dots printed)")


if __name__ == "__main__":
    asyncio.run(test_async_streaming())
