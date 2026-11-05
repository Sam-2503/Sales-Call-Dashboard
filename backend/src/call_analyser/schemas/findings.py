"""Evidence-backed findings and customer signals."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Evidence(BaseModel):
    turn_id: str = Field(pattern=r"^T\d{3,}$")
    speaker: str = Field(min_length=1)
    role: Literal["agent", "customer", "other"]
    quote: str = Field(min_length=1)
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)
    match_score: float = Field(ge=0, le=100)
    attempt: int = Field(ge=0, le=2)

    @model_validator(mode="after")
    def ordered_time(self) -> Evidence:
        if self.start_s >= self.end_s:
            raise ValueError("start_s must be less than end_s")
        return self


class Finding(BaseModel):
    id: str = Field(min_length=1)
    rubric_item_id: str | None = None
    category: str = Field(min_length=1)
    evidence: Evidence | None = None
    model_confidence: float = Field(ge=0, le=1)
    confidence: Literal["high", "medium", "low"] = "medium"


class RubricResult(Finding):
    status: Literal["met", "partial", "missed", "not_applicable"]
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_required_for_positive_results(self) -> RubricResult:
        if self.status in {"met", "partial"} and self.evidence is None:
            raise ValueError("met and partial rubric results require evidence")
        return self


class MissedMoment(Finding):
    rubric_item_id: str = Field(min_length=1)
    what_happened: str = Field(min_length=1)
    severity: Literal["low", "medium", "high", "critical"]
    why_it_hurt: str | None = None
    better_alternative: str | None = None


class SentimentPoint(BaseModel):
    turn_id: str = Field(pattern=r"^T\d{3,}$")
    quote: str = Field(min_length=1)
    sentiment: Literal["positive", "neutral", "negative", "mixed"]


class Objection(BaseModel):
    text: str = Field(min_length=1)
    raised_evidence: Evidence
    resolved: bool
    resolution_evidence: Evidence | None = None

    @model_validator(mode="after")
    def resolution_matches_status(self) -> Objection:
        if self.resolved != (self.resolution_evidence is not None):
            raise ValueError(
                "resolved objections require, and unresolved objections omit, resolution evidence"
            )
        return self


class Commitment(BaseModel):
    party: str = Field(min_length=1)
    what: str = Field(min_length=1)
    due: str = Field(min_length=1)
    evidence: Evidence


class CustomerSignals(BaseModel):
    sentiment_arc: list[SentimentPoint] = Field(default_factory=list, max_length=12)
    objections: list[Objection] = Field(default_factory=list)
    unanswered_questions: list[Evidence] = Field(default_factory=list)
    buying_signals: list[Evidence] = Field(default_factory=list)
    commitments: list[Commitment] = Field(default_factory=list)
    outcome: Literal["advanced", "stalled", "lost", "unclear"] = "unclear"
