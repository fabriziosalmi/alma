"""
Unit tests for the DashboardApp data logic and recovery wizard.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import httpx
import pytest
from rich.layout import Layout

from alma.cli.dashboard import DashboardApp, MAX_CONSECUTIVE_ERRORS

# --- Fixtures ---


@pytest.fixture
def dashboard_app():
    """Provides a non-mocked DashboardApp instance for testing."""
    return DashboardApp(mock=False)


# --- Data Logic and Main Loop Tests ---


def test_initialization(dashboard_app: DashboardApp):
    """Verify app starts with default empty state."""
    assert dashboard_app.api_status == "connecting"
    assert dashboard_app.consecutive_errors == 0
    assert dashboard_app.metrics == {}
    assert dashboard_app.iprs == []


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_update_success_resets_error_counter(mock_client_constructor, dashboard_app: DashboardApp):
    """Verify that a successful API call resets the consecutive_errors counter."""
    dashboard_app.consecutive_errors = 2

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {}

    mock_async_client = AsyncMock()
    mock_async_client.get.side_effect = [mock_response, mock_response]
    dashboard_app.http_client = mock_async_client

    await dashboard_app.update_data()

    assert dashboard_app.consecutive_errors == 0
    assert dashboard_app.api_status == "connected"


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_update_api_connection_failure_increments_counter(
    mock_client_constructor, dashboard_app: DashboardApp
):
    """Mock a connection error and verify the error counter is incremented."""
    mock_async_client = AsyncMock()
    mock_async_client.get.side_effect = httpx.ConnectError("Test connection failure")
    dashboard_app.http_client = mock_async_client

    assert dashboard_app.consecutive_errors == 0
    await dashboard_app.update_data()
    assert dashboard_app.consecutive_errors == 1
    assert dashboard_app.api_status == "Disconnected"


@pytest.mark.asyncio
@patch("alma.cli.dashboard.DashboardApp.run_recovery_wizard")
async def test_run_loop_exits_and_calls_wizard(mock_run_wizard, dashboard_app: DashboardApp):
    """Verify the main loop exits after MAX_CONSECUTIVE_ERRORS and then calls the recovery wizard."""
    with patch.object(dashboard_app, "update_data", new_callable=AsyncMock) as mock_update:

        async def fail_and_increment_error():
            dashboard_app.consecutive_errors += 1

        mock_update.side_effect = fail_and_increment_error

        with patch("alma.cli.dashboard.Live"):
            await dashboard_app.run()

    assert dashboard_app.consecutive_errors == MAX_CONSECUTIVE_ERRORS
    mock_run_wizard.assert_called_once()


# --- Wizard Tests with Correct Patching ---


def test_recovery_wizard_saves_to_env(dashboard_app: DashboardApp):
    """Test the recovery wizard's data collection and saving logic."""
    # Patch targets must be where the objects are LOOKED UP, not where they are defined.
    with patch("alma.cli.dashboard.Prompt.ask") as mock_prompt, patch(
        "alma.cli.dashboard.Confirm.ask"
    ) as mock_confirm, patch("alma.cli.dashboard.find_dotenv") as mock_find_dotenv, patch(
        "alma.cli.dashboard.set_key"
    ) as mock_set_key:
        # Simulate user input and file system behavior
        mock_prompt.side_effect = ["1", "sk-ollama-key"]
        mock_confirm.return_value = True
        mock_find_dotenv.return_value = ".env"  # Ensure it finds a path

        dashboard_app.run_recovery_wizard()

        assert mock_set_key.call_count == 2
        mock_set_key.assert_any_call(".env", "OPENAI_BASE_URL", "http://localhost:11434/v1")
        mock_set_key.assert_any_call(".env", "OPENAI_API_KEY", "sk-ollama-key")


def test_recovery_wizard_handles_custom_url(dashboard_app: DashboardApp):
    """Test the wizard correctly prompts for a custom URL when '4' is selected."""
    with patch("alma.cli.dashboard.Prompt.ask") as mock_prompt, patch(
        "alma.cli.dashboard.Confirm.ask"
    ) as mock_confirm, patch("alma.cli.dashboard.find_dotenv") as mock_find_dotenv, patch(
        "alma.cli.dashboard.set_key"
    ) as mock_set_key:
        mock_prompt.side_effect = ["4", "http://my.custom.endpoint/v1", "custom_api_key"]
        mock_confirm.return_value = True
        mock_find_dotenv.return_value = ".env"

        dashboard_app.run_recovery_wizard()

        assert mock_prompt.call_count == 3  # 1 for menu, 1 for custom URL, 1 for API key
        assert mock_set_key.call_count == 2
        mock_set_key.assert_any_call(".env", "OPENAI_BASE_URL", "http://my.custom.endpoint/v1")
        mock_set_key.assert_any_call(".env", "OPENAI_API_KEY", "custom_api_key")
