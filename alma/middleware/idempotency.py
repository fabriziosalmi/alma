"""
Idempotency Middleware
======================

Ensures that retrying a failed API request multiple times doesn't result in duplicate transactions.
Stores the response of a successful request associated with an Idempotency-Key.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle Idempotency-Key headers.
    """

    def __init__(self, app: ASGIApp, cache_ttl: int = 86400):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        # In-memory cache: {key: {'response': ResponseData, 'timestamp': float}}
        # ResponseData = {'status_code': int, 'headers': dict, 'body': bytes}
        self.cache: dict[str, dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Check for Idempotency-Key header
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        # 2. Check if key exists in cache
        if idempotency_key in self.cache:
            entry = self.cache[idempotency_key]
            # Check TTL
            if time.time() - entry["timestamp"] < self.cache_ttl:
                logger.info(f"Idempotency hit for key: {idempotency_key}")
                cached_resp = entry["response"]
                return Response(
                    content=cached_resp["body"],
                    status_code=cached_resp["status_code"],
                    headers=cached_resp["headers"],
                    media_type=cached_resp["headers"].get("content-type"),
                )
            else:
                # Expired
                del self.cache[idempotency_key]

        # 3. Process request
        response = await call_next(request)

        # 4. Cache response (only for success/client error, not server error usually)
        # And only if it's not a stream (streaming responses are hard to cache)
        # For simplicity, we'll cache 2xx and 4xx.
        if 200 <= response.status_code < 500:
            # We need to read the body to cache it.
            # WARNING: This consumes the iterator. We must reconstruct it.
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Store in cache
            self.cache[idempotency_key] = {
                "timestamp": time.time(),
                "response": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                },
            }

            # Return reconstructed response
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )

        return response
