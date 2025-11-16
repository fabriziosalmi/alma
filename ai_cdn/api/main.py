"""FastAPI application main module."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_cdn.core.config import get_settings
from ai_cdn.core.database import init_db, close_db
from ai_cdn.core.llm_service import initialize_llm, shutdown_llm, warmup_llm
from ai_cdn.api.routes import blueprints, conversation, ipr

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


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
