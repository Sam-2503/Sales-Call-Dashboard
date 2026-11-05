"""Deterministic demo workspace seeding, with no LLM or audio calls."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.auth.tokens import issue_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call
from analyser_api.db.models import Workspace as WorkspaceModel
from analyser_api.services.reports import persist_report
from call_analyser.rubric import load_rubric
from call_analyser.schemas.findings import (
    CustomerSignals,
    Evidence,
    MissedMoment,
    RubricResult,
)
from call_analyser.schemas.report import CallReport, NextSteps, ReportMeta, Scorecard
from call_analyser.schemas.rubric import Rubric, RubricItem


def _evidence(item: RubricItem) -> Evidence:
    return Evidence(
        turn_id="T001",
        speaker="Agent",
        role="agent",
        quote="Demo evidence.",
        start_s=0,
        end_s=1,
        match_score=100,
        attempt=0,
    )


def _report(
    rubric: Rubric,
    settings: Settings,
    *,
    score: int,
    outcome: Literal["advanced", "stalled", "lost", "unclear"],
    index: int,
) -> CallReport:
    statuses: dict[str, Literal["met", "partial", "missed"]] = {}
    results: list[RubricResult] = []
    missed: list[MissedMoment] = []
    for position, item in enumerate(rubric.items):
        # Deterministically spread misses and partials across calls.
        selector = (score + position + index) % 10
        status: Literal["met", "partial", "missed"]
        if selector == 0:
            status = "missed"
        elif selector in (1, 2):
            status = "partial"
        else:
            status = "met"
        statuses[item.id] = status
        evidence = None if status == "missed" else _evidence(item)
        results.append(
            RubricResult(
                id=f"rubric-{item.id}",
                rubric_item_id=item.id,
                category=item.category,
                evidence=evidence,
                model_confidence=0.85,
                confidence="high",
                status=status,
                rationale="Deterministic demo result.",
            )
        )
        if status in ("missed", "partial"):
            missed.append(
                MissedMoment(
                    id=f"missed-{index}-{item.id}",
                    rubric_item_id=item.id,
                    category=item.category,
                    evidence=_evidence(item),
                    model_confidence=0.8,
                    confidence="medium",
                    what_happened="Demo finding for the trends view.",
                    severity="high" if status == "missed" else "medium",
                )
            )
    category_scores: dict[str, float] = {}
    for category in rubric.categories:
        values = [
            rubric.scoring[statuses[item.id]]
            for item in rubric.items
            if item.category == category.id
        ]
        category_scores[category.id] = round(sum(values) / len(values) * 100, 1) if values else 0.0
    overall = round(
        sum(category_scores[category.id] * category.weight for category in rubric.categories),
        1,
    )
    return CallReport(
        status="ok",
        meta=ReportMeta(
            pipeline_version=settings.package.pipeline_version,
            rubric_id=rubric.id,
            rubric_version=rubric.version,
            models={"demo": "deterministic"},
            usage={"est_cost_usd": 0},
        ),
        scorecard=Scorecard(
            overall_score=overall,
            category_scores=category_scores,
            critical_failures=[
                item.id for item in rubric.items if item.critical and statuses[item.id] == "missed"
            ],
        ),
        rubric_results=results,
        missed_moments=missed,
        customer_signals=CustomerSignals(outcome=outcome),
        next_steps=NextSteps(recommended_actions=["Follow up with the prospect."]),
    )


async def seed_demo_workspace(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    *,
    calls: int,
    label: str | None = None,
    reuse: bool = False,
) -> tuple[UUID, str]:
    rubric = load_rubric(settings.rubric_path)
    async with session_factory() as session:
        if reuse and label:
            existing = await session.scalar(
                select(WorkspaceModel).where(WorkspaceModel.label == label)
            )
            if existing is not None:
                return existing.id, issue_token(existing.id, settings)
        workspace = WorkspaceModel(is_demo=True, label=label or f"demo-{uuid4()}")
        session.add(workspace)
        await session.flush()
        me = Agent(workspace_id=workspace.id, name="Me")
        alex = Agent(workspace_id=workspace.id, name="Alex")
        session.add_all((me, alex))
        await session.flush()
        now = datetime.now(UTC)
        rng = random.Random(20260101)
        created: list[UUID] = []
        for index in range(max(0, calls)):
            item = rubric.items[index % len(rubric.items)]
            call_id = uuid4()
            created_at = now - timedelta(days=56) + timedelta(days=index * 4)
            session.add(
                Call(
                    id=call_id,
                    workspace_id=workspace.id,
                    agent_id=me.id if index % 2 == 0 else alex.id,
                    title=f"Demo call {index + 1}",
                    status="completed",
                    audio_key=None,
                    audio_mime=None,
                    audio_sha256=None,
                    audio_bytes=None,
                    duration_s=float(90 + rng.randint(0, 120)),
                    original_filename=None,
                    consent_at=created_at,
                    is_demo=True,
                    rubric_id=rubric.id,
                    rubric_version=rubric.version,
                    created_at=created_at,
                    completed_at=created_at,
                )
            )
            created.append(call_id)
            del item
        await session.commit()
    for index, call_id in enumerate(created):
        report = _report(
            rubric,
            settings,
            score=55 + (index * 7) % 40,
            outcome=("advanced", "stalled", "unclear")[index % 3],
            index=index,
        )
        await persist_report(session_factory, call_id, report)
    return workspace.id, issue_token(workspace.id, settings)
