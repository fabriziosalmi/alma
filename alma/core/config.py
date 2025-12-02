"""Configuration management."""

from __future__ import annotations
import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="ALMA_",
    )

    # Application
    app_name: str = "ALMA"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    api_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Database
    database_url: str = "sqlite+aiosqlite:///./alma.db"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    api_key: str = Field(default="", description="API Key for authentication")

    # LLM
    llm_model_name: str = "Qwen/Qwen2-0.5B"
    llm_device: str = "cpu"
    llm_max_tokens: int = 512
    llm_local_studio_url: str = "http://localhost:1234/v1/chat/completions"
    llm_local_studio_model: str = "qwen/qwen3-1.7b"

    # Engines
    default_engine: str = "fake"
    engine_timeout: int = 300  # 5 minutes

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = False
    metrics_port: int = 9090

    # Infrastructure Pull Request (IPR)
    ipr_enabled: bool = True
    ipr_auto_approve: bool = False
    ipr_require_review: bool = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance
    """
    return settings
