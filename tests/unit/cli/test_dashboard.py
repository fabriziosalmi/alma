"""
Unit tests for the DashboardApp data logic and recovery wizard.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import httpx
import pytest
from rich.layout import Layout

from ai_cdn.cli.dashboard import DashboardApp, MAX_CONSECUTIVE_ERRORS

# --- Fixtures ---

@pytest.fixture
def app():
    """Provides a non-mocked DashboardApp instance for testing."""
    return DashboardApp(mock=False)

# --- Data Logic and Main Loop Tests ---

def test_initialization(app: DashboardApp):
    """Verify app starts with default empty state."""
    assert app.api_status == "connecting"
    assert app.consecutive_errors == 0
    assert app.metrics == {}
    assert app.iprs == []

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_update_success_resets_error_counter(mock_client_constructor, app: DashboardApp):
    """Verify that a successful API call resets the consecutive_errors counter."""
    app.consecutive_errors = 2
    
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {}
    
    mock_async_client = AsyncMock()
    mock_async_client.get.side_effect = [mock_response, mock_response]
    app.http_client = mock_async_client
    
    await app.update_data()
    
    assert app.consecutive_errors == 0
    assert app.api_status == "connected"

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_update_api_connection_failure_increments_counter(mock_client_constructor, app: DashboardApp):
    """Mock a connection error and verify the error counter is incremented."""
    mock_async_client = AsyncMock()
    mock_async_client.get.side_effect = httpx.ConnectError("Test connection failure")
    app.http_client = mock_async_client
    
    assert app.consecutive_errors == 0
    await app.update_data()
    assert app.consecutive_errors == 1
    assert app.api_status == "Disconnected"

@pytest.mark.asyncio
@patch("ai_cdn.cli.dashboard.DashboardApp.run_recovery_wizard")
async def test_run_loop_exits_and_calls_wizard(mock_run_wizard, app: DashboardApp):
    """Verify the main loop exits after MAX_CONSECUTIVE_ERRORS and then calls the recovery wizard."""
    with patch.object(app, "update_data", new_callable=AsyncMock) as mock_update:
        async def fail_and_increment_error():
            app.consecutive_errors += 1
        
        mock_update.side_effect = fail_and_increment_error

        with patch("ai_cdn.cli.dashboard.Live"):
            await app.run()

    assert app.consecutive_errors == MAX_CONSECUTIVE_ERRORS
    mock_run_wizard.assert_called_once()

# --- Wizard Tests with Correct Patching ---

def test_recovery_wizard_saves_to_env(app: DashboardApp):
    """Test the recovery wizard's data collection and saving logic."""
    # Patch targets must be where the objects are LOOKED UP, not where they are defined.
    with patch("ai_cdn.cli.dashboard.Prompt.ask") as mock_prompt, \
         patch("ai_cdn.cli.dashboard.Confirm.ask") as mock_confirm, \
         patch("ai_cdn.cli.dashboard.find_dotenv") as mock_find_dotenv, \
         patch("ai_cdn.cli.dashboard.set_key") as mock_set_key:

        # Simulate user input and file system behavior
        mock_prompt.side_effect = ["1", "sk-ollama-key"]
        mock_confirm.return_value = True
        mock_find_dotenv.return_value = ".env" # Ensure it finds a path

        app.run_recovery_wizard()

        assert mock_set_key.call_count == 2
        mock_set_key.assert_any_call(".env", "OPENAI_BASE_URL", "http://localhost:11434/v1")
        mock_set_key.assert_any_call(".env", "OPENAI_API_KEY", "sk-ollama-key")

def test_recovery_wizard_handles_custom_url(app: DashboardApp):
    """Test the wizard correctly prompts for a custom URL when '4' is selected."""
    with patch("ai_cdn.cli.dashboard.Prompt.ask") as mock_prompt, \
         patch("ai_cdn.cli.dashboard.Confirm.ask") as mock_confirm, \
         patch("ai_cdn.cli.dashboard.find_dotenv") as mock_find_dotenv, \
         patch("ai_cdn.cli.dashboard.set_key") as mock_set_key:

        mock_prompt.side_effect = ["4", "http://my.custom.endpoint/v1", "custom_api_key"]
        mock_confirm.return_value = True
        mock_find_dotenv.return_value = ".env"

        app.run_recovery_wizard()

        assert mock_prompt.call_count == 3 # 1 for menu, 1 for custom URL, 1 for API key
        assert mock_set_key.call_count == 2
        mock_set_key.assert_any_call(".env", "OPENAI_BASE_URL", "http://my.custom.endpoint/v1")
        mock_set_key.assert_any_call(".env", "OPENAI_API_KEY", "custom_api_key")