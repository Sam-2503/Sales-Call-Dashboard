"""Application settings, loaded only on explicit construction."""

from __future__ import annotations

from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunable values used by the pipeline; environment variables override defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Model selection and LLM call policy.
    groq_api_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias=AliasChoices("GROQ_API_KEY", "XAI_API_KEY"),
    )
    chat_provider: str = "groq"
    analysis_model: str = "openai/gpt-oss-20b"
    fast_model: str = "openai/gpt-oss-20b"
    transcribe_model: str = "whisper-large-v3-turbo"
    llm_max_concurrency: int = Field(default=1, ge=1)
    llm_max_retries: int = Field(default=2, ge=0)
    llm_timeout_s: float = Field(default=60, gt=0)

    # Audio ingestion and transcription.
    max_audio_minutes: float = Field(default=5, gt=0)
    max_audio_bytes: int = Field(default=100_000_000, ge=1)
    min_duration_s: float = Field(default=60, ge=0)
    min_words: int = Field(default=150, ge=0)
    transcribe_inline_max_mb: float = Field(default=15, gt=0)
    llm_max_output_tokens: int = Field(default=4096, ge=1)
    fake_mode: bool = False
    work_dir: Path = Path("data/work")

    # Deterministic conversation and audio metrics.
    monologue_gap_s: float = Field(default=2.0, ge=0)
    long_monologue_s: float = Field(default=30.0, gt=0)
    dead_air_s: float = Field(default=3.0, gt=0)
    slow_response_s: float = Field(default=2.5, ge=0)
    silence_db: float = Field(default=-40.0, le=0)

    # Evidence verification, repair, and confidence buckets.
    verify_turn_radius: int = Field(default=1, ge=0)
    verify_min_score: float = Field(default=90, ge=0, le=100)
    repair_max_attempts: int = Field(default=2, ge=0)
    confidence_high_min_match_score: float = Field(default=97, ge=0, le=100)
    confidence_medium_min_match_score: float = Field(default=93, ge=0, le=100)
    confidence_high_min_model_confidence: float = Field(default=0.7, ge=0, le=1)
    confidence_low_max_model_confidence: float = Field(default=0.4, ge=0, le=1)

    # Findings and selection.
    max_missed_moments: int = Field(default=10, ge=1)
    max_excerpt_words: int = Field(default=25, ge=1)

    # Usage accounting, logging, and run provenance.
    log_level: str = "INFO"
    pipeline_version: str = "0.1.0"
