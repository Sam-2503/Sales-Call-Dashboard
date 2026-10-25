"""Application settings, loaded only on explicit construction."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunable values used by the pipeline; environment variables override defaults."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    gemini_api_key: str | None = Field(default=None, repr=False)
    chat_provider: str = "google_genai"
    analysis_model: str = "gemini-2.5-pro"
    fast_model: str = "gemini-2.5-flash"
    transcribe_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    llm_max_concurrency: int = Field(default=4, ge=1)
    llm_max_retries: int = Field(default=2, ge=0)
    llm_timeout_s: float = Field(default=60, gt=0)
    max_audio_minutes: float = Field(default=120, gt=0)
    min_duration_s: float = Field(default=60, ge=0)
    min_words: int = Field(default=150, ge=0)
    turn_gap_s: float = Field(default=1.5, ge=0)
    verify_turn_radius: int = Field(default=1, ge=0)
    verify_min_score: float = Field(default=90, ge=0, le=100)
    repair_max_attempts: int = Field(default=2, ge=0)
    max_missed_moments: int = Field(default=10, ge=1)
    max_excerpt_words: int = Field(default=25, ge=1)
    playbook_grounding: Literal["on", "off"] = "on"
    chroma_path: Path = Path("data/chroma")
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
