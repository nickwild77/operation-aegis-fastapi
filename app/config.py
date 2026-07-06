"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Operation Aegis API"
    app_env: Literal["development", "test", "production"] = "development"

    # No default value: application startup must fail when the token is missing.
    api_token: SecretStr

    database_path: Path = Path("data/aegis.db")
    upload_directory: Path = Path("data/uploads")
    max_upload_size_bytes: int = 1_048_576

    allowed_upload_extensions: tuple[str, ...] = (
        ".txt",
        ".csv",
        ".json",
    )
    allowed_upload_content_types: tuple[str, ...] = (
        "text/plain",
        "text/csv",
        "application/json",
    )

    docs_enabled: bool = True

    @field_validator("api_token")
    @classmethod
    def validate_api_token(cls, value: SecretStr) -> SecretStr:
        """Reject weak or empty API tokens."""
        if len(value.get_secret_value()) < 32:
            raise ValueError("API_TOKEN must contain at least 32 characters")
        return value

    @field_validator("max_upload_size_bytes")
    @classmethod
    def validate_upload_limit(cls, value: int) -> int:
        """Keep the upload limit within reasonable bounds."""
        if not 1 <= value <= 10_485_760:
            raise ValueError("MAX_UPLOAD_SIZE_BYTES must be between 1 and 10485760")
        return value


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings object for the process."""
    return Settings()
