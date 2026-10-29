"""Report persistence and normalized query tables."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from call_analyser.schemas.report import CallReport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analyser_api.db.models import (
    Call,
    CallCategoryScore,
    CallItemResult,
    Report,
    ReportFinding,
)


def _estimate_cost(report: CallReport) -> float | None:
    value = report.meta.usage.get("est_cost_usd")
    return float(value) if isinstance(value, (int, float)) else None


async def persist_report(
    session_factory: async_sessionmaker[AsyncSession],
    call_id: UUID,
    report: CallReport,
) -> None:
    """Store a report and rebuild derived rows in one transaction."""
    async with session_factory() as session, session.begin():
        scorecard = report.scorecard
        await session.merge(
            Report(
                call_id=call_id,
                report=report.model_dump(mode="json"),
                report_status=report.status,
                schema_version=report.schema_version,
                pipeline_version=report.meta.pipeline_version,
                overall_score=scorecard.overall_score if scorecard else None,
                outcome=report.customer_signals.outcome if report.customer_signals else None,
                critical_failure_count=len(scorecard.critical_failures) if scorecard else 0,
                unverified_count=report.unverified_count,
                est_cost_usd=_estimate_cost(report),
                usage=dict(report.meta.usage),
                created_at=datetime.now(UTC),
            )
        )
        await session.execute(delete(CallCategoryScore).where(CallCategoryScore.call_id == call_id))
        await session.execute(delete(CallItemResult).where(CallItemResult.call_id == call_id))
        await session.execute(delete(ReportFinding).where(ReportFinding.call_id == call_id))

        if scorecard is not None:
            session.add_all(
                CallCategoryScore(
                    call_id=call_id,
                    category_id=category_id,
                    score=score,
                )
                for category_id, score in scorecard.category_scores.items()
            )
        session.add_all(
            CallItemResult(
                call_id=call_id,
                rubric_item_id=result.rubric_item_id or result.id,
                category_id=result.category,
                status=result.status,
            )
            for result in report.rubric_results
        )
        session.add_all(
            ReportFinding(
                call_id=call_id,
                finding_id=finding.id,
                kind="missed_moment",
            )
            for finding in report.missed_moments
        )
        session.add_all(
            ReportFinding(
                call_id=call_id,
                finding_id=result.id,
                kind="rubric_result",
            )
            for result in report.rubric_results
        )
        call = await session.get(Call, call_id)
        if call is not None:
            call.status = "completed"
            call.completed_at = datetime.now(UTC)
            call.rubric_id = report.meta.rubric_id
            call.rubric_version = report.meta.rubric_version
