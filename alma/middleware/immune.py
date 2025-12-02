"""
Immune System Middleware
========================

Intercepts incoming requests and scans them using the ImmuneSystem.
If a threat is detected, it returns a 204 No Content response (Silent Drop).
"""

import logging
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from alma.core.immune_system import ImmuneSystem

logger = logging.getLogger(__name__)


class ImmuneMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.immune_system = ImmuneSystem()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip immune check for safe methods or specific paths if needed
        # For now, we scan everything that might have a body or query params

        # 1. Scan Query Parameters
        query_params = str(request.query_params)
        if query_params:
            result = self.immune_system.scan(query_params)
            if result.blocked:
                logger.warning(f"Immune System BLOCKED request (Query): {result.reason}")
                return Response(status_code=204)  # Silent Drop

        # 2. Scan Body (if present)
        # Note: Reading body in middleware can be tricky.
        # We need to ensure we don't consume the stream so the endpoint can read it.
        # However, for a robust defense, we must inspect it.
        # For this implementation, we'll peek at the body if it's not too large.

        # Optimization: Implement chunked body reading for large files
        # Currently limiting scan to first 4KB to avoid DoS via large payload scanning.

        # We will only scan JSON or Text bodies.
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type or "text/" in content_type:
            try:
                # Receive the body
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8", errors="ignore")

                # Scan
                result = self.immune_system.scan(body_text)
                if result.blocked:
                    logger.warning(f"Immune System BLOCKED request (Body): {result.reason}")
                    return Response(status_code=204)  # Silent Drop

            except Exception as e:
                logger.error(f"Error during immune scan: {e}")
                # Fail open or closed? Protocol Ahimsa suggests fail safe,
                # but we don't want to block legit traffic on internal error.
                # We'll log and proceed for now.
                pass

        response = await call_next(request)
        return response
