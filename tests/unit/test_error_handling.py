"""Unit tests for error handling."""

from unittest.mock import MagicMock

import pytest
from fastapi import Request

from alma.core.error_handling import calm_exception_handler


@pytest.mark.asyncio
async def test_calm_exception_handler():
    """Test calm exception handler."""
    # Create mock request
    request = MagicMock(spec=Request)

    # Create test exception
    exc = ValueError("Test error")

    # Call handler
    response = await calm_exception_handler(request, exc)

    # Verify response
    assert response.status_code == 500
    assert "status" in response.body.decode()
    assert "error" in response.body.decode()
