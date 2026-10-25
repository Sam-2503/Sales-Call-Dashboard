"""Top-level call-report contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from schemas.findings import CustomerSignals, MissedMoment, RubricResult
from schemas.metrics import AudioMetrics
from schemas.transcript import Transcript


class Scorecard(BaseModel):
    overall_score: float | None = Field(default=None, ge=0, le=100)
    category_scores: dict[str, float] = Field(default_factory=dict)
    critical_failures: list[str] = Field(default_factory=list)


class CoachingItem(BaseModel):
    finding_id: str = Field(min_length=1)
    explanation: str = Field(min_length=1)
    practice_drill: str = Field(min_length=1)


class Coaching(BaseModel):
    top_fixes: list[CoachingItem] = Field(default_factory=list, max_length=3)
    strength: str | None = None


class NextSteps(BaseModel):
    follow_up_message: str | None = None
    recommended_actions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def bounded_follow_up(self) -> NextSteps:
        if self.follow_up_message and len(self.follow_up_message.split()) > 150:
            raise ValueError("follow_up_message must contain at most 150 words")
        return self


class ReportMeta(BaseModel):
    pipeline_version: str = Field(min_length=1)
    rubric_id: str | None = None
    rubric_version: str | None = None
    playbook_identity: dict[str, Any] | None = None
    models: dict[str, str] = Field(default_factory=dict)
    prompt_ids: dict[str, str] = Field(default_factory=dict)
    audio_sha256: str | None = None
    duration_s: float | None = Field(default=None, ge=0)
    usage: dict[str, int | float] = Field(default_factory=dict)
    stage_latency_s: dict[str, float] = Field(default_factory=dict)


class DebugReport(BaseModel):
    dropped_findings: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_passage_ids: dict[str, list[str]] = Field(default_factory=dict)


class CallReport(BaseModel):
    schema_version: str = "1.0"
    status: Literal["ok", "insufficient_data"]
    reason: str | None = None
    meta: ReportMeta
    transcript: Transcript | None = None
    scorecard: Scorecard | None = None
    audio_metrics: AudioMetrics | None = None
    rubric_results: list[RubricResult] = Field(default_factory=list)
    missed_moments: list[MissedMoment] = Field(default_factory=list)
    customer_signals: CustomerSignals | None = None
    next_steps: NextSteps | None = None
    coaching: Coaching | None = None
    unverified_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)
    debug: DebugReport = Field(default_factory=DebugReport)

    @model_validator(mode="after")
    def coaching_references_known_finding(self) -> CallReport:
        if self.coaching is not None:
            finding_ids = {item.id for item in self.missed_moments}
            unknown = {item.finding_id for item in self.coaching.top_fixes} - finding_ids
            if unknown:
                raise ValueError(f"coaching references unknown finding ids: {sorted(unknown)}")
        return self
