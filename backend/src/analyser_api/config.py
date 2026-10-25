"""Backend configuration loaded explicitly from environment variables."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Deployment settings for the HTTP service."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analyser"
    jwt_secret: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = Field(default_factory=list)
    max_upload_mb: int = Field(default=100, ge=1)
    request_timeout_s: float = Field(default=30, gt=0)
    log_level: str = "INFO"

    @field_validator("jwt_secret")
    @classmethod
    def require_production_secret(cls, value: str | None, info: object) -> str | None:
        if getattr(info, "data", {}).get("environment") == "prod" and (
            value is None or len(value) < 32
        ):
            raise ValueError("JWT_SECRET must contain at least 32 characters in production")
        return value
