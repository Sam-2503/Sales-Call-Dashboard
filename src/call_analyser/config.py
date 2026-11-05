"""Application settings, loaded only on explicit construction."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunable values used by the pipeline; environment variables override defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Model selection and LLM call policy.
    xai_api_key: str | None = Field(default=None, repr=False)
    chat_provider: str = "xai"
    # Lowest-cost current xAI text model; use one model to keep routing simple.
    analysis_model: str = "grok-4.20-0309-non-reasoning"
    fast_model: str = "grok-4.20-0309-non-reasoning"
    transcribe_model: str = "grok-voice-transcribe-2.0"
    embedding_model: str = "unavailable"
    llm_max_concurrency: int = Field(default=4, ge=1)
    llm_max_retries: int = Field(default=2, ge=0)
    llm_timeout_s: float = Field(default=60, gt=0)

    # Audio ingestion and transcription.
    max_audio_minutes: float = Field(default=5, gt=0)
    max_audio_bytes: int = Field(default=100_000_000, ge=1)
    min_duration_s: float = Field(default=60, ge=0)
    min_words: int = Field(default=150, ge=0)
    transcribe_inline_max_mb: float = Field(default=15, gt=0)
    transcribe_max_output_tokens: int = Field(default=16_384, ge=1)
    llm_max_output_tokens: int = Field(default=4096, ge=1)
    role_probe_seconds: float = Field(default=90, gt=0)
    turn_gap_s: float = Field(default=1.5, ge=0)
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

    # Findings, selection, and grounding.
    max_missed_moments: int = Field(default=10, ge=1)
    max_excerpt_words: int = Field(default=25, ge=1)
    playbook_grounding: Literal["on", "off"] = "off"

    # Playbook extraction, indexing, and retrieval.
    chroma_path: Path = Path("data/chroma")
    embedding_manifest_name: str = "playbook_manifest.json"
    chunk_target_tokens: int = Field(default=400, ge=1)
    chunk_max_tokens: int = Field(default=600, ge=1)
    chunk_overlap_tokens: int = Field(default=60, ge=0)
    token_estimate_factor: float = Field(default=1.3, gt=0)
    playbook_max_empty_page_ratio: float = Field(default=0.2, ge=0, le=1)
    embedding_dim: int = Field(default=768, ge=1)
    embed_batch_size: int = Field(default=32, ge=1)
    embed_max_concurrency: int = Field(default=4, ge=1)
    query_embed_cache_size: int = Field(default=256, ge=0)
    playbook_top_k: int = Field(default=4, ge=1)
    playbook_min_score: float = Field(default=0, ge=0, le=1)

    # Usage accounting, logging, and run provenance.
    pricing_path: Path = Path("config/pricing.yaml")
    log_level: str = "INFO"
    log_transcripts: bool = False
    pipeline_version: str = "0.1.0"
    prompt_versions: dict[str, str] = Field(default_factory=dict)

    @field_validator("chunk_max_tokens")
    @classmethod
    def maximum_allows_target(cls, value: int, info: ValidationInfo) -> int:
        target = info.data.get("chunk_target_tokens")
        if isinstance(target, int) and value < target:
            raise ValueError("chunk_max_tokens must be at least chunk_target_tokens")
        return value
