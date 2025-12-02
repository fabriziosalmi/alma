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
    Global exception handler that sanitizes panic and returns a calm response.
    """
    # Log the full traceback internally for Ops
    error_id = str(hash(str(exc)))  # Simple ID for correlation
    logger.error(f"System Panic (ID: {error_id}): {exc}")
    logger.error(traceback.format_exc())

    # Medic Persona Response
    # We don't use the LLM here to avoid recursive failures if the LLM is the cause.
    # We use a static but empathetic template.
    
    medic_response = {
        "status": "error",
        "persona": "MEDIC",
        "message": "I've detected a disturbance in the system processing.",
        "diagnosis": "The operation encountered an unexpected anomaly.",
        "prescription": "I have stabilized the session. Please try your request again, or check the system status if the issue persists.",
        "reference_id": error_id,
        "technical_details": str(exc) if "Dev" in str(type(exc)) else None # Only show details if explicitly safe
    }

    return JSONResponse(
        status_code=500,
        content=medic_response
    )
