"""
Empathetic Error Handling
=========================

Replaces technical tracebacks with calm, helpful feedback.
Uses the "Medic Persona" to guide the user when things go wrong.
"""

from __future__ import annotations

import logging
import traceback

from fastapi import Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def calm_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Global exception handler for API responses only.

    In debug mode: Shows full stack traces
    In production: Shows calm, user-friendly messages
    """
    from alma.core.config import get_settings

    settings = get_settings()

    # Log the full traceback internally for Ops
    error_id = str(hash(str(exc)))  # Simple ID for correlation
    logger.error(f"System Error (ID: {error_id}): {exc}")
    logger.error(traceback.format_exc())

    # Debug mode: Show full stack trace
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error_id": error_id,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "debug_mode": True,
            },
        )

    # Production mode: Calm response for users
    medic_response = {
        "status": "error",
        "message": "The operation encountered an unexpected error.",
        "suggestion": "Please try your request again, or check the system status if the issue persists.",
        "reference_id": error_id,
    }

    return JSONResponse(status_code=500, content=medic_response)
