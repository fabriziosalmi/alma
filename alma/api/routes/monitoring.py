"""API routes for metrics and monitoring."""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from alma.middleware.metrics import get_metrics_collector, get_prometheus_metrics
from alma.middleware.rate_limit import get_rate_limiter

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MetricsSummary(BaseModel):
    """Metrics summary response."""

    uptime_seconds: float
    timestamp: str
    custom_metrics: Dict[str, Any]


class RateLimitStats(BaseModel):
    """Rate limit statistics."""

    total_requests: int
    total_blocked: int
    block_rate: float
    active_clients: int
    requests_per_minute_limit: int
    burst_size: int
    top_clients: list[Dict[str, Any]]


class HealthStatus(BaseModel):
    """Health check status."""

    status: str
    uptime: float
    version: str
    components: Dict[str, str]


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


@router.get("/health/detailed", response_model=HealthStatus)
async def detailed_health() -> HealthStatus:
    """
    Detailed health check with component status.

    Returns:
        Health status
    """
    collector = get_metrics_collector()

    # Check components
    components = {
        "api": "healthy",
        "database": "healthy",  # TODO: Check actual DB connection
        "llm": "healthy",  # TODO: Check LLM availability
        "rate_limiter": "healthy",
    }

    return HealthStatus(
        status="healthy", uptime=collector.get_uptime(), version="0.1.0", components=components
    )


@router.get("/stats/overview")
async def system_overview() -> Dict[str, Any]:
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
            "avg_response_time_ms": 0,  # TODO: Calculate from metrics
            "requests_per_second": 0,  # TODO: Calculate from metrics
        },
    }
