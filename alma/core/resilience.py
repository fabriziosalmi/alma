"""
Resilience Patterns
===================

Implements Circuit Breaker and Retry patterns to improve system reliability.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreakerOpenException(Exception):
    """Raised when the circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit Breaker implementation.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                logger.info(f"Circuit '{self.name}' attempting recovery (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit '{self.name}' recovered (CLOSED)")
                self.reset()

            return result

        except self.expected_exceptions as e:
            self.record_failure()
            logger.warning(f"Circuit '{self.name}' recorded failure: {e}")
            raise e

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(f"Circuit '{self.name}' opened due to failures")
                self.state = CircuitState.OPEN

    def reset(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0


class Retrier:
    """
    Exponential Backoff with Jitter implementation.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await self.call(func, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        import asyncio
        import random

        attempt = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as e:
                attempt += 1
                if attempt >= self.max_attempts:
                    logger.warning(f"Retrier gave up after {attempt} attempts: {e}")
                    raise e

                delay = min(self.max_delay, self.base_delay * (2 ** (attempt - 1)))
                if self.jitter:
                    delay = delay * (0.5 + random.random())

                logger.info(
                    f"Retrying in {delay:.2f}s (Attempt {attempt}/{self.max_attempts}) due to: {e}"
                )
                await asyncio.sleep(delay)
