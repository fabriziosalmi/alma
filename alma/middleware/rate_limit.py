"""Rate limiting middleware for API protection."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

import redis.asyncio as redis
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Distributed Rate Limiter using Redis with Token Bucket algorithm.
    Falls back to in-memory implementation if Redis is unavailable.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379", enabled: bool = True):
        self.enabled = enabled
        # Default limits: (tokens, refill_rate_per_second)
        self.default_limits = (10, 1.0)  # 10 requests burst, 1 req/s refill
        self.ip_limits: dict[str, tuple[int, float]] = {}
        self.endpoint_limits: dict[str, tuple[int, float]] = {}

        # Redis client
        self.redis: redis.Redis | None = None
        self.redis_url = redis_url
        self._redis_available = False

        # In-memory fallback
        self.buckets: dict[str, float] = defaultdict(lambda: 0.0)
        self.last_update: dict[str, float] = defaultdict(time.time)

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        if not self.enabled:
            return

        try:
            self.redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self.redis.ping()  # type: ignore[misc]
            self._redis_available = True
            logger.info(f"RateLimiter connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.warning(
                f"RateLimiter failed to connect to Redis: {e}. Using in-memory fallback."
            )
            self._redis_available = False

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

    def set_limit(self, ip: str, limit: int, rate: float) -> None:
        """Set custom limit for an IP."""
        self.ip_limits[ip] = (limit, rate)

    async def is_rate_limited(self, request: Request) -> tuple[bool, float]:
        """
        Check if request is rate limited.
        Returns (is_limited, retry_after).
        """
        if not self.enabled:
            return False, 0.0

        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Determine limits
        limit, rate = self.ip_limits.get(ip, self.default_limits)

        key = f"rate_limit:{ip}:{path}"
        now = time.time()

        if self._redis_available and self.redis:
            try:
                # Redis Token Bucket Implementation using Lua script for atomicity
                # Keys:
                #   tokens_key: Current tokens available
                #   timestamp_key: Last update timestamp
                tokens_key = f"{key}:tokens"
                timestamp_key = f"{key}:ts"

                # Script:
                # 1. Get current tokens and last timestamp
                # 2. Calculate refill based on time passed
                # 3. Update tokens (min(limit, current + refill))
                # 4. If tokens >= 1, decrement and return allowed (1)
                # 5. Else return denied (0) and retry time

                script = """
                local tokens_key = KEYS[1]
                local ts_key = KEYS[2]
                local limit = tonumber(ARGV[1])
                local rate = tonumber(ARGV[2])
                local now = tonumber(ARGV[3])
                local cost = 1

                local current_tokens = tonumber(redis.call('get', tokens_key) or limit)
                local last_ts = tonumber(redis.call('get', ts_key) or now)

                local delta = math.max(0, now - last_ts)
                local refill = delta * rate

                current_tokens = math.min(limit, current_tokens + refill)

                if current_tokens >= cost then
                    current_tokens = current_tokens - cost
                    redis.call('set', tokens_key, current_tokens)
                    redis.call('set', ts_key, now)
                    -- Expire keys after enough time to fully refill to save space
                    local ttl = math.ceil(limit / rate)
                    redis.call('expire', tokens_key, ttl)
                    redis.call('expire', ts_key, ttl)
                    return {1, 0}
                else
                    local wait = (cost - current_tokens) / rate
                    return {0, wait}
                end
                """

                result = await self.redis.eval(  # type: ignore[misc]
                    script, 2, tokens_key, timestamp_key, limit, rate, now
                )
                allowed = bool(result[0])
                wait_time = float(result[1])

                if allowed:
                    return False, 0.0
                else:
                    return True, wait_time

            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}. Falling back to memory.")
                # Fall through to in-memory check

        # In-memory fallback (Token Bucket)
        # Check existence before accessing to avoid defaultdict creation
        if key not in self.buckets:
            current_tokens: float = float(limit)
            last_ts = now
        else:
            current_tokens = self.buckets[key]
            last_ts = self.last_update[key]

            delta = now - last_ts
            refill = delta * rate
            current_tokens = min(limit, current_tokens + refill)

        if current_tokens >= 1.0:
            self.buckets[key] = current_tokens - 1.0
            self.last_update[key] = now
            return False, 0.0
        else:
            # Calculate wait time
            wait_time = (1.0 - current_tokens) / rate
            return True, wait_time

    async def get_stats(self) -> dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "total_requests": 0,  # TODO: Implement tracking
            "total_blocked": 0,
            "block_rate": 0.0,
            "active_clients": len(self.ip_limits),
            "requests_per_minute_limit": (
                int(self.default_limits[0] / (self.default_limits[1] / 60.0))
                if self.default_limits[1] > 0
                else 0
            ),
            "burst_size": self.default_limits[0],
            "top_clients": [],
        }


class EndpointRateLimiter:
    """
    Rate limiter with per-endpoint limits.

    Allows different rate limits for different endpoints.
    """

    def __init__(self, default_rpm: int = 60):
        """
        Initialize endpoint rate limiter.

        Args:
            default_rpm: Default requests per minute
        """
        self.default_rpm = default_rpm
        self.endpoint_limits: dict[str, int] = {}
        self.limiters: dict[str, RateLimiter] = {}

    def set_endpoint_limit(self, endpoint: str, rpm: int) -> None:
        """
        Set rate limit for specific endpoint.

        Args:
            endpoint: Endpoint path pattern
            rpm: Requests per minute
        """
        self.endpoint_limits[endpoint] = rpm
        # The new RateLimiter takes (limit, rate) where rate is per second
        # rpm / 60.0 gives requests per second
        self.limiters[endpoint] = RateLimiter(enabled=True)  # Initialize with enabled=True
        self.limiters[endpoint].default_limits = (
            max(10, rpm // 6),
            rpm / 60.0,
        )  # Set default limits for this specific limiter instance

    def _get_limiter(self, request: Request) -> RateLimiter:
        """
        Get rate limiter for request.

        Args:
            request: FastAPI request

        Returns:
            Appropriate rate limiter
        """
        path = request.url.path

        # Check for specific endpoint limits
        for endpoint, limiter in self.limiters.items():
            if path.startswith(endpoint):
                return limiter

        # Use default limiter
        if "default" not in self.limiters:
            self.limiters["default"] = RateLimiter(enabled=True)
            self.limiters["default"].default_limits = (
                max(10, self.default_rpm // 6),
                self.default_rpm / 60.0,
            )

        return self.limiters["default"]

    async def check_rate_limit(self, request: Request) -> JSONResponse | None:
        """
        Check rate limit for request.

        Args:
            request: FastAPI request

        Returns:
            JSONResponse if rate limited, None otherwise
        """
        limiter = self._get_limiter(request)

        # Initialize the specific limiter if it hasn't been yet
        if limiter.redis is None and limiter.enabled:
            await limiter.initialize()

        is_limited, retry_after = await limiter.is_rate_limited(request)  # type: ignore[misc]

        if is_limited:
            # Attempt to get the effective RPM for the message
            effective_rpm = self.default_rpm
            for endpoint, rpm_limit in self.endpoint_limits.items():
                if request.url.path.startswith(endpoint):
                    effective_rpm = rpm_limit
                    break

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Max {effective_rpm} requests per minute.",
                    "retry_after": int(retry_after) + 1,
                    "limit": effective_rpm,
                    "window": "1 minute",
                },
                headers={
                    "Retry-After": str(int(retry_after) + 1),
                    "X-RateLimit-Limit": str(effective_rpm),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + int(retry_after) + 1),
                },
            )

        # Approximate remaining and reset for headers
        effective_rpm = self.default_rpm
        for endpoint, rpm_limit in self.endpoint_limits.items():
            if request.url.path.startswith(endpoint):
                effective_rpm = rpm_limit
                break

        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(effective_rpm),
            "X-RateLimit-Remaining": "1",  # Placeholder
            "X-RateLimit-Reset": str(int(time.time()) + 60),
        }

        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits."""

    def __init__(self, app: ASGIApp, limiter: EndpointRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)

        rate_limit_response = await self.limiter.check_rate_limit(request)

        if rate_limit_response:
            return rate_limit_response

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        if hasattr(request.state, "rate_limit_headers"):
            for key, value in request.state.rate_limit_headers.items():
                response.headers[key] = value

        return response


# Global rate limiter instance
_global_limiter: EndpointRateLimiter | None = None


def get_rate_limiter() -> EndpointRateLimiter:
    """
    Get global rate limiter instance.

    Returns:
        Rate limiter instance
    """
    global _global_limiter

    if _global_limiter is None:
        _global_limiter = EndpointRateLimiter(default_rpm=60)

        # Set specific endpoint limits
        _global_limiter.set_endpoint_limit("/api/v1/conversation/chat-stream", 20)
        _global_limiter.set_endpoint_limit("/api/v1/conversation/generate-blueprint", 30)
        _global_limiter.set_endpoint_limit("/api/v1/tools/execute", 40)
        _global_limiter.set_endpoint_limit("/api/v1/blueprints/", 100)

    return _global_limiter


async def rate_limit_middleware(request: Request, call_next: Callable) -> Any:
    """
    Middleware to apply rate limiting to requests.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response
    """
    # Skip rate limiting for health checks and metrics
    if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
        return await call_next(request)

    limiter = get_rate_limiter()

    # Check rate limit
    rate_limit_response = await limiter.check_rate_limit(request)
    if rate_limit_response:
        return rate_limit_response

    # Process request
    response = await call_next(request)

    # Add rate limit headers
    if hasattr(request.state, "rate_limit_headers"):
        for key, value in request.state.rate_limit_headers.items():
            response.headers[key] = value

    return response
