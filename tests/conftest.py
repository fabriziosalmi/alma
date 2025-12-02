"""Pytest configuration and shared fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alma.models.blueprint import Base

# Disable authentication by default for all tests
# Test modules that need auth (like test_auth.py) must override this
os.environ.setdefault("ALMA_AUTH_ENABLED", "false")


@pytest.fixture
def valid_api_key():
    """Provide a valid API key for authenticated tests."""
    return "test-api-key-12345"


@pytest.fixture
def auth_headers(valid_api_key):
    """Provide authentication headers for API requests."""
    return {"X-API-Key": valid_api_key}


@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
