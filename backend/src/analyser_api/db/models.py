"""PostgreSQL persistence model for the analysis service."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def uuid_column() -> Mapped[UUID]:
    return mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)


def timestamp_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Workspace(Base):
    __tablename__ = "workspaces"
    id: Mapped[UUID] = uuid_column()
    created_at: Mapped[datetime] = timestamp_column()
    last_activity_at: Mapped[datetime] = timestamp_column()
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[UUID] = uuid_column()
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = timestamp_column()


class Call(Base):
    __tablename__ = "calls"
    id: Mapped[UUID] = uuid_column()
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    agent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL")
    )
    title: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    audio_key: Mapped[str | None] = mapped_column(String(500))
    audio_mime: Mapped[str | None] = mapped_column(String(120))
    audio_sha256: Mapped[str | None] = mapped_column(String(64))
    audio_bytes: Mapped[int | None] = mapped_column(BigInteger)
    duration_s: Mapped[float | None]
    original_filename: Mapped[str | None] = mapped_column(String(255))
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rubric_id: Mapped[str | None] = mapped_column(String(120))
    rubric_version: Mapped[str | None] = mapped_column(String(40))
    reanalysis_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = timestamp_column()
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[UUID] = uuid_column()
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    available_at: Mapped[datetime] = timestamp_column()
    percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(80))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_message: Mapped[str | None] = mapped_column(Text)
    options: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    locked_by: Mapped[str | None] = mapped_column(String(120))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = timestamp_column()
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class JobEvent(Base):
    __tablename__ = "job_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    percent: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_s: Mapped[float | None]
    detail: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    ts: Mapped[datetime] = timestamp_column()


class Report(Base):
    __tablename__ = "reports"
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True
    )
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    report_status: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(40), nullable=False)
    overall_score: Mapped[float | None]
    outcome: Mapped[str | None] = mapped_column(String(40))
    critical_failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unverified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    est_cost_usd: Mapped[float | None]
    usage: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = timestamp_column()


class CallCategoryScore(Base):
    __tablename__ = "call_category_scores"
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True
    )
    category_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    score: Mapped[float | None]


class CallItemResult(Base):
    __tablename__ = "call_item_results"
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True
    )
    rubric_item_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class ReportFinding(Base):
    __tablename__ = "report_findings"
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True
    )
    finding_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("call_id", "finding_id"),)
    id: Mapped[UUID] = uuid_column()
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    finding_id: Mapped[str] = mapped_column(String(120), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = timestamp_column()
    updated_at: Mapped[datetime] = timestamp_column()


class StageCache(Base):
    __tablename__ = "stage_cache"
    call_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = timestamp_column()


Index("ix_calls_workspace_created", Call.workspace_id, Call.created_at.desc())
Index("ix_jobs_status_available", Job.status, Job.available_at)
Index("ix_job_events_job_id_id", JobEvent.job_id, JobEvent.id)
Index("ix_call_item_results_rubric_item_id", CallItemResult.rubric_item_id)
Index("ix_reports_created_at", Report.created_at)
Index(
    "uq_active_job_per_call",
    Job.call_id,
    unique=True,
    postgresql_where=text("status IN ('queued', 'running')"),
)
