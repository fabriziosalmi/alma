"""Configuration management for AI-CDN."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI-CDN"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    api_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_cdn.db"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Security
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60

    # LLM
    llm_model_name: str = "Qwen/Qwen2-0.5B"
    llm_device: str = "cpu"
    llm_max_tokens: int = 512

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
