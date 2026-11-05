"""Deterministic audio-metric contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TimelineFlag(BaseModel):
    kind: Literal[
        "dead_air", "overlap", "fast_pace", "filler_cluster", "slow_response", "long_monologue"
    ]
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    speaker: str | None = None
    detail: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_time(self) -> TimelineFlag:
        if self.start_s >= self.end_s:
            raise ValueError("start_s must be less than end_s")
        return self


class AudioMetrics(BaseModel):
    duration_s: float = Field(ge=0)
    timing_resolution: Literal["segment_interpolated", "word"] = "segment_interpolated"
    agent_talk_ratio: float | None = Field(default=None, ge=0, le=1)
    customer_talk_ratio: float | None = Field(default=None, ge=0, le=1)
    agent_customer_talk_ratio: float | None = Field(default=None, ge=0)
    silence_ratio: float | None = Field(default=None, ge=0, le=1)
    overlap_ratio: float | None = Field(default=None, ge=0, le=1)
    agent_words_per_minute: float | None = Field(default=None, ge=0)
    customer_words_per_minute: float | None = Field(default=None, ge=0)
    filler_count: int = Field(default=0, ge=0)
    filler_rate_agent: float | None = Field(default=None, ge=0)
    filler_rate_customer: float | None = Field(default=None, ge=0)
    longest_monologue_s: float | None = Field(default=None, ge=0)
    longest_monologue_start_s: float | None = Field(default=None, ge=0)
    longest_monologue_end_s: float | None = Field(default=None, ge=0)
    longest_monologue_turn_ids: list[str] = Field(default_factory=list)
    response_delay_median_s: float | None = Field(default=None, ge=0)
    response_delay_p90_s: float | None = Field(default=None, ge=0)
    interruptions_unavailable_reason: str = (
        "Transcript segments are sequential; overlapping speech is not measurable in v1."
    )
    timeline_flags: list[TimelineFlag] = Field(default_factory=list)
