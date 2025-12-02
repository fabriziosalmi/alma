"""FastAPI application main module."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alma.api.routes import blueprints, conversation, ipr, monitoring, templates, tools
from alma.core.config import get_settings
from alma.core.database import close_db, init_db
from alma.core.error_handling import calm_exception_handler
from alma.core.llm_service import initialize_llm, shutdown_llm, warmup_llm
from alma.middleware.immune import ImmuneMiddleware
from alma.middleware.metrics import metrics_middleware
from alma.middleware.rate_limit import rate_limit_middleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    await init_db()

    # Initialize LLM (optional - will use MockLLM if unavailable)
    try:
        await initialize_llm()
        # Warmup LLM to reduce first-request latency
        await warmup_llm()
    except Exception as e:
        print(f"LLM initialization skipped: {e}")

    yield

    # Shutdown
    await close_db()
    await shutdown_llm()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Infrastructure as Conversation platform",
    debug=settings.debug,
    lifespan=lifespan,
)

# Register Empathetic Error Handler
app.add_exception_handler(Exception, calm_exception_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(blueprints.router, prefix=settings.api_prefix)
app.include_router(conversation.router, prefix=settings.api_prefix)
app.include_router(ipr.router, prefix=settings.api_prefix)
app.include_router(tools.router, prefix=settings.api_prefix)
app.include_router(templates.router, prefix=settings.api_prefix)
app.include_router(monitoring.router, prefix=settings.api_prefix)

# Add middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(metrics_middleware)
app.add_middleware(ImmuneMiddleware)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "name": settings.app_name,
        "status": "operational",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    from alma.middleware.metrics import get_prometheus_metrics

    return get_prometheus_metrics()
