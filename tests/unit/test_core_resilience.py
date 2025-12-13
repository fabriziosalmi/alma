"""Unit tests for Resilience patterns."""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from alma.core.resilience import CircuitBreaker, Retrier, CircuitState, CircuitBreakerOpenException

class TestCircuitBreaker:
    
    @pytest.mark.asyncio
    async def test_circuit_state_transitions(self):
        """Test CLOSED -> OPEN -> HALF_OPEN -> CLOSED flow."""
        cb = CircuitBreaker("test-cb", failure_threshold=2, recovery_timeout=10)
        func = AsyncMock()

        # 1. Normal operation (CLOSED)
        func.return_value = "success"
        assert await cb.call(func) == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

        # 2. Failure counting (CLOSED)
        func.side_effect = ValueError("fail")
        with pytest.raises(ValueError):
            await cb.call(func)
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED

        # 3. Trip circuit (OPEN)
        with pytest.raises(ValueError):
            await cb.call(func)
        assert cb.failure_count == 2
        assert cb.state == CircuitState.OPEN

        # 4. Fail fast (OPEN)
        # Verify it raises CircuitBreakerOpenException immediately without calling func
        func.reset_mock()
        with pytest.raises(CircuitBreakerOpenException):
            await cb.call(func)
        func.assert_not_called()

        # 5. Recovery check (HALF_OPEN)
        # Mock time to pass recovery timeout
        with patch("alma.core.resilience.time.time") as mock_time:
            # Current time needs to be > last_failure + recovery
            # last_failure is set by real time in step 3.
            # So let's force expected values.
            cb.last_failure_time = 100
            mock_time.return_value = 200 # > 100 + 10
            
            # 5a. Probe call succeeds -> CLOSED
            func.side_effect = None
            func.return_value = "recovered"
            
            assert await cb.call(func) == "recovered"
            assert cb.state == CircuitState.CLOSED
            assert cb.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_half_open_failure(self):
        """Test HALF_OPEN -> OPEN on failure."""
        cb = CircuitBreaker("test-cb", failure_threshold=2, recovery_timeout=10)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = 0
        
        func = AsyncMock(side_effect=ValueError("still failing"))

        with patch("alma.core.resilience.time.time", return_value=100):
            # Should enter HALF_OPEN, call func, fail, then go back to OPEN
            with pytest.raises(ValueError):
                await cb.call(func)
            
            assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test using CircuitBreaker as a decorator."""
        cb = CircuitBreaker("decorator-test", failure_threshold=1)
        
        @cb
        async def protected_func():
            return "ok"
            
        assert await protected_func() == "ok"


class TestRetrier:

    @pytest.mark.asyncio
    async def test_retry_success_first_try(self):
        """Test success without retries."""
        retrier = Retrier(max_attempts=3)
        func = AsyncMock(return_value="ok")
        
        assert await retrier.call(func) == "ok"
        assert func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_eventual_success(self):
        """Test success after retries."""
        retrier = Retrier(max_attempts=3, base_delay=0.1, jitter=False)
        func = AsyncMock(side_effect=[ValueError("fail"), ValueError("fail"), "success"])
        
        start_time = time.time()
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
             assert await retrier.call(func) == "success"
             
             assert func.call_count == 3
             assert mock_sleep.call_count == 2 # Sleep before retry 2 and 3

    @pytest.mark.asyncio
    async def test_max_attempts_exceeded(self):
        """Test failure after max attempts."""
        retrier = Retrier(max_attempts=2, base_delay=0.1, jitter=False)
        func = AsyncMock(side_effect=ValueError("persistent failure"))
        
        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ValueError):
                await retrier.call(func)
        
        assert func.call_count == 2
    
    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test using Retrier as a decorator."""
        retrier = Retrier(max_attempts=2)
        
        @retrier
        async def unstable_func():
            return "ok"
            
        assert await unstable_func() == "ok"
