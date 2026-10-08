"""Application configuration with pydantic-settings.

All configuration is loaded from environment variables (with sensible defaults).
The settings object is the single source of truth for runtime configuration.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    APP_NAME: str = "Bulk Certificate Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./certificate_generator.db"
    DB_ECHO: bool = False

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_REDIS: bool = False  # Set True to use Redis-backed background queue

    # --- Background processing ---
    BACKGROUND_WORKER_THREADS: int = 2
    MAX_CONCURRENT_JOBS: int = 4

    # --- Storage ---
    CERTIFICATE_STORAGE_DIR: str = "./generated_certs"
    CERTIFICATE_RETENTION_HOURS: int = 72

    # --- Generation ---
    MAX_RECIPIENTS_PER_JOB: int = 5000
    DEFAULT_TEMPLATE_STYLE: str = "modern"
    CERTIFICATE_WIDTH_PX: int = 1190
    CERTIFICATE_HEIGHT_PX: int = 842  # A4 landscape

    # --- Pagination ---
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # --- Rate limiting ---
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # --- Security ---
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALLOWED_HOSTS: list[str] = ["*"]

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()