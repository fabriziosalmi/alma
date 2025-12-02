"""API routes for metrics and monitoring."""

from __future__ import annotations
import time
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from alma.core.database import get_session
from alma.core.llm_service import get_orchestrator
from alma.middleware.metrics import get_metrics_collector, get_prometheus_metrics
from alma.middleware.rate_limit import get_rate_limiter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MetricsSummary(BaseModel):
    """Metrics summary response."""

    uptime_seconds: float
    timestamp: str
    custom_metrics: dict[str, Any]


class RateLimitStats(BaseModel):
    """Rate limit statistics."""

    total_requests: int
    total_blocked: int
    block_rate: float
    active_clients: int
    requests_per_minute_limit: int
    burst_size: int
    top_clients: list[dict[str, Any]]


class HealthStatus(BaseModel):
    """Health check status."""

    status: str
    uptime: float
    version: str
    components: dict[str, str]


@router.get("/metrics/summary", response_model=MetricsSummary)
async def get_metrics_summary() -> MetricsSummary:
    """
    Get human-readable metrics summary.

    Returns:
        Metrics summary
    """
    collector = get_metrics_collector()
    summary = collector.get_summary()

    return MetricsSummary(**summary)


@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """
    Get Prometheus-formatted metrics.

    Returns:
        Prometheus metrics in text format
    """
    return get_prometheus_metrics()


@router.get("/rate-limit/stats", response_model=RateLimitStats)
async def get_rate_limit_stats() -> RateLimitStats:
    """
    Get rate limiting statistics.

    Returns:
        Rate limit stats
    """
    limiter = get_rate_limiter()
    stats = (
        limiter.limiters.get("default").get_stats()
        if "default" in limiter.limiters
        else {
            "total_requests": 0,
            "total_blocked": 0,
            "block_rate": 0.0,
            "active_clients": 0,
            "requests_per_minute_limit": 60,
            "burst_size": 10,
            "top_clients": [],
        }
    )

    return RateLimitStats(**stats)


async def check_database_health() -> dict[str, Any]:
    """
    Check database connectivity and health.

    Returns:
        Database health status
    """
    try:
        start = time.time()
        async with get_session() as session:
            await session.execute(text("SELECT 1"))
        response_time = (time.time() - start) * 1000  # Convert to ms

        return {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


async def check_llm_health() -> dict[str, Any]:
    """
    Check LLM service availability.

    Returns:
        LLM health status
    """
    try:
        orchestrator = await get_orchestrator()
        if orchestrator and orchestrator.llm:
            return {
                "status": "healthy",
                "model": getattr(orchestrator.llm, "model_name", "unknown"),
            }
        else:
            return {
                "status": "unhealthy",
                "error": "LLM not initialized",
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


@router.get("/health/detailed")
async def detailed_health() -> dict[str, Any]:
    """
    Detailed health check with component status.

    Returns:
        Health status with HTTP status code based on health
    """
    collector = get_metrics_collector()

    # Check all components
    db_health = await check_database_health()
    llm_health = await check_llm_health()

    components = {
        "api": {"status": "healthy"},
        "database": db_health,
        "llm": llm_health,
        "rate_limiter": {"status": "healthy"},
    }

    # Determine overall status
    unhealthy_components = [
        name for name, comp in components.items() if comp.get("status") == "unhealthy"
    ]

    if len(unhealthy_components) >= 2 or "database" in unhealthy_components:
        overall_status = "unhealthy"
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    elif len(unhealthy_components) == 1:
        overall_status = "degraded"
        http_status = status.HTTP_200_OK
    else:
        overall_status = "healthy"
        http_status = status.HTTP_200_OK

    response = {
        "status": overall_status,
        "uptime_seconds": collector.get_uptime(),
        "version": "0.4.3",
        "components": components,
    }

    # Return appropriate status code
    from fastapi.responses import JSONResponse
    return JSONResponse(content=response, status_code=http_status)


@router.get("/stats/overview")
async def system_overview() -> dict[str, Any]:
    """
    Get comprehensive system overview.

    Returns:
        System statistics
    """
    collector = get_metrics_collector()
    limiter = get_rate_limiter()

    rate_limit_stats = (
        limiter.limiters.get("default").get_stats() if "default" in limiter.limiters else {}
    )

    return {
        "system": {
            "uptime_seconds": collector.get_uptime(),
            "version": "0.1.0",
            "status": "operational",
        },
        "rate_limiting": {
            "total_requests": rate_limit_stats.get("total_requests", 0),
            "total_blocked": rate_limit_stats.get("total_blocked", 0),
            "block_rate": rate_limit_stats.get("block_rate", 0.0),
        },
        "performance": {
            "avg_response_time_ms": 0,  # Calculated by Prometheus
            "requests_per_second": 0,  # Calculated by Prometheus
        },
        "health": {
            "database": (await check_database_health()).get("status", "unknown"),
            "llm": (await check_llm_health()).get("status", "unknown"),
        },
    }
