"""Tests for database module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from alma.core.database import get_session, init_db, close_db, engine


class TestDatabase:
    """Tests for database utilities."""

    @pytest.mark.asyncio
    async def test_get_session(self) -> None:
        """Test getting a database session."""
        async for session in get_session():
            assert isinstance(session, AsyncSession)
            break  # Just test we can get one

    @pytest.mark.asyncio
    async def test_init_db(self) -> None:
        """Test database initialization."""
        # This should not raise any errors
        await init_db()

    @pytest.mark.asyncio
    async def test_close_db(self) -> None:
        """Test closing database connections."""
        # This should not raise any errors
        await close_db()

    def test_engine_exists(self) -> None:
        """Test that engine is created."""
        assert engine is not None
