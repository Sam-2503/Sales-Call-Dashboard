"""SQL-only trends, weak spots, and benchmarks over stored reports."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, distinct, func, select

from analyser_api.config import Settings
from analyser_api.db.models import (
    Call,
    CallCategoryScore,
    CallItemResult,
    Report,
)
from analyser_api.deps import Database, Workspace, get_rubric, get_settings
from call_analyser.schemas.rubric import Rubric

router = APIRouter(prefix="/api/v1", tags=["trends"])


def _rubric_conditions(rubric: Rubric) -> tuple[Any, ...]:
    return (Call.rubric_id == rubric.id, Call.rubric_version == rubric.version)


def _base(*, rubric: Rubric, workspace_id: UUID) -> Any:
    return (
        select(Call.id, Call.created_at, Call.title, Report.overall_score)
        .join(Report, Report.call_id == Call.id)
        .where(
            Call.workspace_id == workspace_id,
            Report.report_status == "ok",
            *_rubric_conditions(rubric),
        )
    )


@router.get("/trends/scores")
async def trend_scores(
    workspace_id: Workspace,
    db: Database,
    rubric: Annotated[Rubric, Depends(get_rubric)],
    agent_id: UUID | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> dict[str, Any]:
    query = _base(rubric=rubric, workspace_id=workspace_id)
    if agent_id is not None:
        query = query.where(Call.agent_id == agent_id)
    if since is not None:
        query = query.where(Call.created_at >= since)
    if until is not None:
        query = query.where(Call.created_at <= until)
    calls = query.order_by(Call.created_at.asc()).limit(limit).subquery()
    rows = await db.execute(
        select(
            calls.c.id,
            calls.c.created_at,
            calls.c.title,
            calls.c.overall_score,
            CallCategoryScore.category_id,
            CallCategoryScore.score,
        )
        .outerjoin(CallCategoryScore, CallCategoryScore.call_id == calls.c.id)
        .order_by(calls.c.created_at.asc())
    )
    points: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.id)
        point = points.setdefault(
            key,
            {
                "call_id": row.id,
                "created_at": row.created_at,
                "title": row.title,
                "overall_score": row.overall_score,
                "category_scores": {},
            },
        )
        if row.category_id is not None:
            point["category_scores"][row.category_id] = row.score
    return {
        "rubric": {"id": rubric.id, "version": rubric.version},
        "categories": [{"id": item.id, "name": item.name} for item in rubric.categories],
        "points": list(points.values()),
        "n": len(points),
    }


@router.get("/trends/weak-spots")
async def weak_spots(
    workspace_id: Workspace,
    db: Database,
    rubric: Annotated[Rubric, Depends(get_rubric)],
    settings: Annotated[Settings, Depends(get_settings)],
    agent_id: UUID | None = None,
    last_n: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, Any]:
    query = _base(rubric=rubric, workspace_id=workspace_id).with_only_columns(Call.id)
    if agent_id is not None:
        query = query.where(Call.agent_id == agent_id)
    calls = query.order_by(Call.created_at.desc()).limit(last_n).subquery()
    n_calls = int(await db.scalar(select(func.count()).select_from(calls)) or 0)
    if n_calls < settings.trends_min_calls:
        return {
            "available": False,
            "reason": f"at least {settings.trends_min_calls} analysed calls are required",
            "n_calls": n_calls,
            "items": [],
        }
    rows = await db.execute(
        select(
            CallItemResult.rubric_item_id,
            CallItemResult.category_id,
            func.count(distinct(CallItemResult.call_id)).label("applicable_calls"),
            func.count(
                distinct(
                    case(
                        (
                            CallItemResult.status.in_(("missed", "partial")),
                            CallItemResult.call_id,
                        )
                    )
                )
            ).label("issue_calls"),
            func.count(
                distinct(case((CallItemResult.status == "missed", CallItemResult.call_id)))
            ).label("missed_calls"),
        )
        .where(CallItemResult.call_id.in_(select(calls.c.id)))
        .group_by(CallItemResult.rubric_item_id, CallItemResult.category_id)
    )
    items = {item.id: item for item in rubric.items}
    categories = {category.id: category.name for category in rubric.categories}
    output = []
    for row in rows:
        item = items.get(row.rubric_item_id)
        if item is None or not row.issue_calls:
            continue
        output.append(
            {
                "item_id": row.rubric_item_id,
                "title": item.title,
                "category": categories.get(row.category_id, row.category_id),
                "issue_calls": int(row.issue_calls),
                "missed_calls": int(row.missed_calls),
                "applicable_calls": int(row.applicable_calls),
                "n_calls": n_calls,
            }
        )
    output.sort(key=lambda item: (-item["issue_calls"], item["item_id"]))
    return {
        "available": True,
        "rubric": {"id": rubric.id, "version": rubric.version},
        "n_calls": n_calls,
        "items": output,
    }


@router.get("/benchmarks")
async def benchmarks(
    call_id: UUID,
    workspace_id: Workspace,
    db: Database,
    rubric: Annotated[Rubric, Depends(get_rubric)],
) -> dict[str, Any]:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    report = await db.scalar(
        select(Report).where(Report.call_id == call_id, Report.report_status == "ok")
    )
    if report is None:
        raise HTTPException(status_code=409, detail="not_ready")
    category_rows = await db.execute(
        select(CallCategoryScore.category_id, CallCategoryScore.score).where(
            CallCategoryScore.call_id == call_id
        )
    )
    target_categories = {row.category_id: row.score for row in category_rows}

    def conditions(*, exclude_id: UUID | None = None) -> Any:
        values = [
            Call.workspace_id == workspace_id,
            Call.id != call_id,
            Report.report_status == "ok",
            *_rubric_conditions(rubric),
        ]
        if exclude_id is not None:
            values.append(Call.id == exclude_id)
        return values

    agent_best: dict[str, Any] | None = None
    if call.agent_id is not None:
        best = (
            await db.execute(
                select(Call.id, Report.overall_score)
                .join(Report, Report.call_id == Call.id)
                .where(*conditions(), Call.agent_id == call.agent_id)
                .order_by(Report.overall_score.desc().nullslast())
                .limit(1)
            )
        ).first()
        if best is not None:
            best_categories = await db.execute(
                select(CallCategoryScore.category_id, CallCategoryScore.score).where(
                    CallCategoryScore.call_id == best.id
                )
            )
            agent_best = {
                "call_id": best.id,
                "overall_score": best.overall_score,
                "category_scores": {row.category_id: row.score for row in best_categories},
            }

    team_count = int(
        await db.scalar(
            select(func.count(distinct(Call.agent_id)))
            .join(Report, Report.call_id == Call.id)
            .where(*conditions())
        )
        or 0
    )
    team_average: dict[str, Any] | None = None
    team_reason: str | None = None
    if team_count < 2:
        team_reason = "fewer than two agents have another analysed call"
    else:
        overall = await db.scalar(
            select(func.avg(Report.overall_score))
            .join(Call, Call.id == Report.call_id)
            .where(*conditions())
        )
        team_rows = await db.execute(
            select(
                CallCategoryScore.category_id,
                func.avg(CallCategoryScore.score),
            )
            .join(Call, Call.id == CallCategoryScore.call_id)
            .join(Report, Report.call_id == Call.id)
            .where(*conditions())
            .group_by(CallCategoryScore.category_id)
        )
        team_average = {
            "overall_score": overall,
            "category_scores": {row.category_id: float(row[1]) for row in team_rows},
        }
    categories = []
    for category in rubric.categories:
        categories.append(
            {
                "id": category.id,
                "name": category.name,
                "call": target_categories.get(category.id),
                "agent_best": (
                    agent_best["category_scores"].get(category.id) if agent_best else None
                ),
                "team_average": (
                    team_average["category_scores"].get(category.id) if team_average else None
                ),
            }
        )
    return {
        "call_id": call_id,
        "rubric": {"id": rubric.id, "version": rubric.version},
        "overall": {
            "call": report.overall_score,
            "agent_best": agent_best["overall_score"] if agent_best else None,
            "team_average": team_average["overall_score"] if team_average else None,
            "team_reason": team_reason,
        },
        "categories": categories,
        "n": {
            "agent": 1 if agent_best else 0,
            "team": team_count,
        },
    }
