"""Unit tests for core config."""

import os
from unittest.mock import patch
import pytest
from alma.core.config import Settings, get_settings


class TestSettings:
    def test_default_settings(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_prefix == "/api/v1"
        assert settings.environment == "development"

    def test_settings_from_env(self):
        """Test settings loaded from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ALMA_API_HOST": "127.0.0.1",
                "ALMA_API_PORT": "9000",
                "ALMA_ENVIRONMENT": "production",
            },
        ):
            settings = Settings()
            assert settings.api_host == "127.0.0.1"
            assert settings.api_port == 9000
            assert settings.environment == "production"

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
