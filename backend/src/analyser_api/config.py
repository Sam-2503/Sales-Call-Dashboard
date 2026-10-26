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
    db_pooler: bool = False
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_connect_retries: int = Field(default=3, ge=0)
    jwt_secret: str | None = Field(default=None, repr=False)
    cors_origins: list[str] = Field(default_factory=list)
    max_upload_mb: int = Field(default=25, ge=1)
    daily_calls_per_workspace: int = Field(default=5, ge=1)
    daily_calls_global: int = Field(default=100, ge=1)
    storage_backend: Literal["local", "s3"] = "local"
    storage_dir: str = "data/audio"
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: str | None = Field(default=None, repr=False)
    s3_secret_access_key: str | None = Field(default=None, repr=False)
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
