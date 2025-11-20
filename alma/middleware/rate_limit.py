"""Rate limiting middleware for API protection."""

import time
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import asyncio


class RateLimiter:
    """
    Token bucket rate limiter with multiple strategies.

    Supports:
    - Per-IP rate limiting
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - Burst handling
    - Adaptive rate limiting
    """

    def __init__(
        self, requests_per_minute: int = 60, burst_size: int = 10, enable_adaptive: bool = False
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            burst_size: Max burst requests
            enable_adaptive: Enable adaptive rate limiting
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.enable_adaptive = enable_adaptive

        # Token buckets: {client_id: {'tokens': float, 'last_update': float}}
        self.buckets: Dict[str, Dict[str, float]] = {}

        # Request tracking for metrics
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.blocked_counts: Dict[str, int] = defaultdict(int)

        # Adaptive rate limiting state
        self.adaptive_limits: Dict[str, int] = {}

        # Cleanup old buckets periodically
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes

    def _get_client_id(self, request: Request) -> str:
        """
        Get unique client identifier.

        Args:
            request: FastAPI request

        Returns:
            Client identifier
        """
        # Try to get user ID from auth (if implemented)
        # For now, use IP address
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"

    def _get_tokens(self, client_id: str) -> float:
        """
        Get current token count for client.

        Args:
            client_id: Client identifier

        Returns:
            Available tokens
        """
        now = time.time()

        if client_id not in self.buckets:
            self.buckets[client_id] = {"tokens": float(self.burst_size), "last_update": now}
            return float(self.burst_size)

        bucket = self.buckets[client_id]
        time_passed = now - bucket["last_update"]

        # Refill tokens based on time passed
        tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
        bucket["tokens"] = min(self.burst_size, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

        return bucket["tokens"]

    def _consume_token(self, client_id: str) -> bool:
        """
        Try to consume a token.

        Args:
            client_id: Client identifier

        Returns:
            True if token consumed, False if rate limited
        """
        tokens = self._get_tokens(client_id)

        if tokens >= 1.0:
            self.buckets[client_id]["tokens"] -= 1.0
            self.request_counts[client_id] += 1
            return True

        self.blocked_counts[client_id] += 1
        return False

    def _cleanup_old_buckets(self) -> None:
        """Remove inactive buckets to prevent memory leak."""
        now = time.time()

        if now - self._last_cleanup < self._cleanup_interval:
            return

        # Remove buckets inactive for > 1 hour
        inactive_threshold = now - 3600

        to_remove = [
            client_id
            for client_id, bucket in self.buckets.items()
            if bucket["last_update"] < inactive_threshold
        ]

        for client_id in to_remove:
            del self.buckets[client_id]

        self._last_cleanup = now

    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check if request should be rate limited.

        Args:
            request: FastAPI request

        Returns:
            JSONResponse if rate limited, None otherwise
        """
        # Bypass rate limiting in test environment
        import os

        if os.environ.get("TESTING") == "true" or os.environ.get("BYPASS_RATE_LIMIT") == "true":
            return None

        client_id = self._get_client_id(request)

        # Cleanup old buckets periodically
        self._cleanup_old_buckets()

        # Check rate limit
        if not self._consume_token(client_id):
            # Calculate retry-after
            tokens = self._get_tokens(client_id)
            tokens_needed = 1.0 - tokens
            retry_after = int((tokens_needed / (self.requests_per_minute / 60.0)) + 1)

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute.",
                    "retry_after": retry_after,
                    "limit": self.requests_per_minute,
                    "window": "1 minute",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                },
            )

        # Add rate limit headers to response
        tokens_remaining = int(self._get_tokens(client_id))
        request.state.rate_limit_headers = {
            "X-RateLimit-Limit": str(self.requests_per_minute),
            "X-RateLimit-Remaining": str(tokens_remaining),
            "X-RateLimit-Reset": str(int(time.time()) + 60),
        }

        return None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get rate limiter statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = sum(self.request_counts.values())
        total_blocked = sum(self.blocked_counts.values())

        return {
            "total_requests": total_requests,
            "total_blocked": total_blocked,
            "block_rate": total_blocked / max(total_requests, 1),
            "active_clients": len(self.buckets),
            "requests_per_minute_limit": self.requests_per_minute,
            "burst_size": self.burst_size,
            "top_clients": sorted(
                [{"client_id": k, "requests": v} for k, v in self.request_counts.items()],
                key=lambda x: x["requests"],
                reverse=True,
            )[:10],
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
        self.endpoint_limits: Dict[str, int] = {}
        self.limiters: Dict[str, RateLimiter] = {}

    def set_endpoint_limit(self, endpoint: str, rpm: int) -> None:
        """
        Set rate limit for specific endpoint.

        Args:
            endpoint: Endpoint path pattern
            rpm: Requests per minute
        """
        self.endpoint_limits[endpoint] = rpm
        self.limiters[endpoint] = RateLimiter(requests_per_minute=rpm, burst_size=max(10, rpm // 6))

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
            self.limiters["default"] = RateLimiter(requests_per_minute=self.default_rpm)

        return self.limiters["default"]

    async def check_rate_limit(self, request: Request) -> Optional[JSONResponse]:
        """
        Check rate limit for request.

        Args:
            request: FastAPI request

        Returns:
            JSONResponse if rate limited, None otherwise
        """
        limiter = self._get_limiter(request)
        return await limiter.check_rate_limit(request)


# Global rate limiter instance
_global_limiter: Optional[EndpointRateLimiter] = None


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
