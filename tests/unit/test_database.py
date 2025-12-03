"""Unit tests for database module."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from alma.core.database import get_session, init_db, close_db


@pytest.mark.asyncio
async def test_get_session():
    """Test get_session generator."""
    # Test the generator yields a session
    gen = get_session()
    session = await gen.__anext__()

    # Verify session was yielded
    assert session is not None

    # Close the generator
    try:
        await gen.aclose()
    except StopAsyncIteration:
        pass


@pytest.mark.asyncio
async def test_init_db():
    """Test database initialization."""
    with patch("alma.core.database.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_engine.begin = AsyncMock(return_value=mock_conn)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)

        await init_db()

        # Verify begin was called
        mock_engine.begin.assert_called_once()


@pytest.mark.asyncio
async def test_close_db():
    """Test database close."""
    with patch("alma.core.database.engine") as mock_engine:
        mock_engine.dispose = AsyncMock()

        await close_db()

        # Verify dispose was called
        mock_engine.dispose.assert_called_once()
