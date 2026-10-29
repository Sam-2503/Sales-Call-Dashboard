"""Backend configuration loaded explicitly from environment variables.

The backend owns deployment concerns (HTTP, database, auth, storage, queueing,
limits).  Analysis tunables stay in the package's own ``Settings``; the
``package`` field composes that model instead of copying its fields here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Self, cast

from call_analyser.config import Settings as PackageSettings
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Deployment settings for the HTTP service and its worker."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Runtime and edge behaviour.
    environment: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = Field(default=7860, ge=1, le=65535)
    request_timeout_s: float = Field(default=30, gt=0)
    cors_origins: list[str] = Field(default_factory=list)
    trusted_proxy_count: int = Field(default=1, ge=0)
    static_dir: Path | None = None

    # Database.  The pooler DSN is for the app; migrations use the direct DSN.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analyser"
    database_url_direct: str | None = None
    db_pooler: bool = False
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=5, ge=0)
    db_connect_retries: int = Field(default=3, ge=0)

    # Authentication and rate limiting.
    jwt_secret: str | None = Field(default=None, repr=False)
    jwt_ttl_days: int = Field(default=30, ge=1)
    media_token_ttl_s: int = Field(default=600, ge=1)
    workspace_rate_limit_per_hour: int = Field(default=20, ge=1)
    upload_rate_limit_per_hour: int = Field(default=30, ge=1)

    # Daily quotas and spend control.
    daily_calls_per_workspace: int = Field(default=5, ge=1)
    daily_calls_global: int = Field(default=100, ge=1)
    daily_budget_usd: float = Field(default=1.0, ge=0)
    max_upload_mb: int = Field(default=25, ge=1)
    max_reanalyses_per_call: int = Field(default=3, ge=0)
    allowed_audio_extensions: list[str] = Field(
        default_factory=lambda: ["wav", "mp3", "m4a", "ogg", "flac", "webm"]
    )

    # Demo and trends.
    demo_workspaces_per_ip_per_day: int = Field(default=3, ge=0)
    demo_seed_calls: int = Field(default=8, ge=0)
    trends_min_calls: int = Field(default=3, ge=1)

    # Retention and housekeeping.
    retention_days: int = Field(default=30, ge=1)
    workspace_idle_days: int = Field(default=60, ge=1)
    demo_idle_days: int = Field(default=3, ge=1)
    janitor_interval_s: int = Field(default=3600, ge=1)

    # Audio storage.  Keys never contain client filenames.
    storage_backend: Literal["local", "s3"] = "local"
    storage_dir: Path = Path("data/audio")
    s3_bucket: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: str | None = Field(default=None, repr=False)
    s3_secret_access_key: str | None = Field(default=None, repr=False)
    playbook_artifact_prefix: str | None = None

    # Worker and event delivery.
    worker_enabled: bool = True
    worker_mode: Literal["thread", "inline", "off"] = "thread"
    worker_poll_interval_s: float = Field(default=2, gt=0)
    worker_heartbeat_interval_s: float = Field(default=15, gt=0)
    worker_stale_after_s: float = Field(default=60, gt=0)
    worker_concurrency: int = Field(default=2, ge=1)
    job_max_attempts: int = Field(default=2, ge=1)
    job_stale_s: int = Field(default=60, ge=1)
    job_heartbeat_s: int = Field(default=10, ge=1)
    shutdown_grace_s: int = Field(default=20, ge=0)
    sse_poll_s: float = Field(default=0.7, gt=0)
    sse_keepalive_s: float = Field(default=15, gt=0)

    # Analysis integration.  The package remains authoritative for audio limits.
    rubric_path: Path = Path("../rubrics/sales_v1.yaml")
    playbook_path: Path | None = None
    package: PackageSettings = Field(default_factory=PackageSettings, repr=False)

    # Operator surface.
    admin_token: str | None = Field(default=None, repr=False)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Allow either a JSON list or the common comma-separated format."""
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = json.loads(text)
            if not isinstance(parsed, list):
                raise ValueError("CORS_ORIGINS must be a list")
            return cast(list[str], parsed)
        return [item.strip() for item in text.split(",") if item.strip()]

    @model_validator(mode="after")
    def require_production_secret(self) -> Self:
        if self.environment != "dev" and (not self.jwt_secret or len(self.jwt_secret) < 32):
            raise ValueError("JWT_SECRET must contain at least 32 characters outside dev")
        return self
