"""HTTP API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from call_analyser.schemas.report import CallReport
from pydantic import BaseModel, Field


class WorkspaceResponse(BaseModel):
    workspace_id: UUID
    token: str
    expires_at: datetime


class WorkspaceInfo(BaseModel):
    workspace_id: UUID
    created_at: datetime
    last_activity_at: datetime
    calls_today: int
    quota_remaining: int = 0
    is_demo: bool = False
    label: str | None = None


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AgentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AgentResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime


class CallUploadResponse(BaseModel):
    call_id: UUID
    job_id: UUID
    status: str


class CallSummary(BaseModel):
    id: UUID
    title: str | None
    status: str
    created_at: datetime
    duration_s: float | None
    overall_score: float | None = None
    outcome: str | None = None
    report_status: str | None = None
    percent: int | None = None
    has_audio: bool = False
    is_demo: bool = False
    agent_id: UUID | None = None
    agent_name: str | None = None


class CallListResponse(BaseModel):
    items: list[CallSummary]
    next_cursor: str | None = None


class CallResponse(CallSummary):
    original_filename: str | None = None
    consent_at: datetime
    audio_mime: str | None = None
    audio_bytes: int | None = None
    reanalysis_count: int = 0
    completed_at: datetime | None = None
    job: JobResponse | None = None


class ReanalyseRequest(BaseModel):
    agent_speaker: str | None = None


class JobActionResponse(BaseModel):
    call_id: UUID
    job_id: UUID
    status: str


class JobResponse(BaseModel):
    id: UUID
    call_id: UUID
    status: str
    attempts: int
    max_attempts: int
    percent: int
    current_stage: str | None
    error_code: str | None
    error_message: str | None
    queue_position: int | None = None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class JobEventResponse(BaseModel):
    id: int
    stage: str
    status: str
    percent: int
    elapsed_s: float | None
    detail: dict[str, Any]
    ts: datetime


class AudioUrlResponse(BaseModel):
    url: str


class FeedbackCreate(BaseModel):
    finding_id: str = Field(min_length=1, max_length=120)
    kind: str = Field(min_length=1, max_length=20)
    verdict: Literal["helpful", "disagree"]
    comment: str | None = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    id: UUID
    call_id: UUID
    finding_id: str
    kind: str
    verdict: str
    comment: str | None
    created_at: datetime
    updated_at: datetime


ReportResponse = CallReport
