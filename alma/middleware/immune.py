"""
Simplified Immune System Middleware
===================================

Uses standard validation instead of academic entropy calculations:
- L0: Regex patterns for known attacks
- L1: Pydantic strict validation
- L2: Input size limits
- L3: Rate limiting (via separate middleware)
"""

import logging
import re
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ImmuneMiddleware(BaseHTTPMiddleware):
    """Simplified immune system using standard validation."""

    # Known malicious patterns (L0 - Regex Guard)
    MALICIOUS_PATTERNS = [
        r"(?i)(union\s+select|drop\s+table|exec\s*\()",  # SQL injection
        r"(?i)(<script|javascript:|onerror=)",  # XSS
        r"(?i)(\.\.\/|\.\.\\)",  # Path traversal
        r"(?i)(eval\(|exec\(|__import__)",  # Code injection
    ]

    # Input size limits (L2)
    MAX_QUERY_LENGTH = 2048  # 2KB
    MAX_BODY_SIZE = 1024 * 1024  # 1MB

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.patterns = [re.compile(p) for p in self.MALICIOUS_PATTERNS]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Scan request using standard validation."""

        # L0: Check query parameters
        query_params = str(request.query_params)
        if query_params:
            # Size limit
            if len(query_params) > self.MAX_QUERY_LENGTH:
                logger.warning(f"Blocked: Query too long ({len(query_params)} bytes)")
                return Response(status_code=400, content=b"Query too long")

            # Pattern matching
            if self._contains_malicious_pattern(query_params):
                logger.warning(f"Blocked: Malicious pattern in query")
                return Response(status_code=400, content=b"Invalid input")

        # L1: Check body (if present)
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type or "text/" in content_type:
            try:
                body_bytes = await request.body()

                # Size limit
                if len(body_bytes) > self.MAX_BODY_SIZE:
                    logger.warning(f"Blocked: Body too large ({len(body_bytes)} bytes)")
                    return Response(status_code=413, content=b"Payload too large")

                # Pattern matching
                body_text = body_bytes.decode("utf-8", errors="ignore")
                if self._contains_malicious_pattern(body_text):
                    logger.warning(f"Blocked: Malicious pattern in body")
                    return Response(status_code=400, content=b"Invalid input")

            except Exception as e:
                logger.error(f"Error during validation: {e}")
                # Fail open for internal errors (don't block legitimate traffic)
                pass

        response = await call_next(request)
        return response

    def _contains_malicious_pattern(self, text: str) -> bool:
        """Check if text contains known malicious patterns."""
        for pattern in self.patterns:
            if pattern.search(text):
                return True
        return False
