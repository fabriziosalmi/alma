"""Unit tests for the DashboardApp data logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rich.layout import Layout

from ai_cdn.cli.dashboard import DashboardApp

pytestmark = pytest.mark.asyncio

@pytest.fixture
def app():
    """Provides a non-mocked DashboardApp instance for testing."""
    return DashboardApp(mock=False)

async def test_initialization(app: DashboardApp):
    """Verify app starts with default empty state."""
    assert app.api_status == "connecting"
    assert app.metrics == {}
    assert app.iprs == []
    assert len(app.logs) == 0
    assert app.mock is False

async def test_layout_generation(app: DashboardApp):
    """Call generate_layout() and ensure it returns a valid Layout object."""
    layout = app.generate_layout()
    assert isinstance(layout, Layout)
    assert layout["header"] is not None
    assert layout["main"] is not None
    assert layout["footer"] is not None
    assert layout["main"]["brain"] is not None
    assert layout["main"]["action"] is not None

@patch("httpx.AsyncClient")
async def test_update_success(mock_client_constructor, app: DashboardApp):
    """
    Mock a 200 OK response with valid JSON. Verify app state is updated correctly.
    """
    mock_metrics = {"llm": {"tokens_per_second": 100}, "system": {"cpu_usage": 50.0}}
    mock_iprs = [{"id": 1, "title": "Test IPR", "status": "pending_approval"}]

    mock_metrics_response = MagicMock()
    mock_metrics_response.raise_for_status = MagicMock()
    mock_metrics_response.json.return_value = mock_metrics
    
    mock_iprs_response = MagicMock()
    mock_iprs_response.raise_for_status = MagicMock()
    mock_iprs_response.json.return_value = mock_iprs

    mock_async_client = AsyncMock()
    # Let the side_effect be an iterable of the final results
    mock_async_client.get.side_effect = [mock_metrics_response, mock_iprs_response]

    app.http_client = mock_async_client

    await app.update_data()

    assert app.api_status == "connected"
    assert app.metrics["system"]["cpu_usage"] == 50.0
    assert len(app.iprs) == 1
    assert app.iprs[0]["title"] == "Test IPR"
    assert "Data refreshed" in app.logs[-1]

@patch("httpx.AsyncClient")
async def test_update_api_connection_failure(mock_client_constructor, app: DashboardApp):
    """
    Mock a connection error. Verify the app handles it gracefully.
    """
    mock_async_client = AsyncMock()
    mock_async_client.get.side_effect = httpx.ConnectError("Test connection failure")
    app.http_client = mock_async_client
    
    initial_metrics = app.metrics.copy()

    await app.update_data()

    assert app.api_status == "Disconnected"
    assert "API connection failed" in app.logs[-1]
    assert app.metrics == initial_metrics

@patch("httpx.AsyncClient")
async def test_update_api_http_failure(mock_client_constructor, app: DashboardApp):
    """
    Mock a 500 error. Verify the app handles it gracefully.
    """
    mock_500_response = MagicMock()
    mock_500_response.status_code = 500
    # The gather() call will return the exception, which is then checked
    # So we don't need to mock raise_for_status here.
    
    mock_async_client = AsyncMock()
    # We will mock the first call to fail and the second to succeed
    # to test the gather() logic properly.
    mock_async_client.get.side_effect = [
        httpx.HTTPStatusError(
            "Server Error", request=MagicMock(), response=mock_500_response
        ),
        MagicMock() # A successful response for the second call
    ]
    app.http_client = mock_async_client
    
    await app.update_data()

    assert app.api_status == "Disconnected"
    # This assertion is tricky because of gather. A more robust test
    # would be to check that raise_for_status was called on the failing response.
    # But for now, checking the log is sufficient.
    assert "An unexpected error occurred" in app.logs[-1]