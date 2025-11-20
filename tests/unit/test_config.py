"""Tests for configuration module."""

import os
from alma.core.config import Settings, get_settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_settings(self) -> None:
        """Test default settings values."""
        settings = Settings()

        assert settings.app_name == "ALMA"
        assert settings.debug is False
        assert settings.database_echo is False
        assert settings.log_level == "INFO"

    def test_database_url_default(self) -> None:
        """Test default database URL is SQLite."""
        settings = Settings()
        assert "sqlite" in settings.database_url
        assert "alma.db" in settings.database_url

    def test_get_settings_singleton(self) -> None:
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_allowed_origins(self) -> None:
        """Test allowed origins configuration."""
        settings = Settings()
        assert isinstance(settings.api_cors_origins, list)

    def test_api_configuration(self) -> None:
        """Test API configuration defaults."""
        settings = Settings()
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.api_prefix == "/api/v1"
