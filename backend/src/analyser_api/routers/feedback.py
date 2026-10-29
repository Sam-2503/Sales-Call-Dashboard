"""Workspace-scoped feedback endpoints for report findings."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from analyser_api.db.models import Call, Feedback, ReportFinding
from analyser_api.deps import Database, Workspace
from analyser_api.schemas.api import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/api/v1/calls/{call_id}/feedback", tags=["feedback"])


def serialize(feedback: Feedback) -> FeedbackResponse:
    return FeedbackResponse(
        id=feedback.id,
        call_id=feedback.call_id,
        finding_id=feedback.finding_id,
        kind=feedback.kind,
        verdict=feedback.verdict,
        comment=feedback.comment,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at,
    )


async def get_call(call_id: UUID, workspace_id: UUID, db: Database) -> Call:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return call


@router.get("", response_model=list[FeedbackResponse])
async def list_feedback(
    call_id: UUID, workspace_id: Workspace, db: Database
) -> list[FeedbackResponse]:
    await get_call(call_id, workspace_id, db)
    feedback = await db.scalars(
        select(Feedback).where(Feedback.call_id == call_id).order_by(Feedback.created_at)
    )
    return [serialize(item) for item in feedback]


@router.put("/{finding_id}", response_model=FeedbackResponse)
async def upsert_feedback(
    call_id: UUID,
    finding_id: str,
    body: FeedbackCreate,
    workspace_id: Workspace,
    db: Database,
) -> FeedbackResponse:
    await get_call(call_id, workspace_id, db)
    if body.finding_id != finding_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="finding_id does not match the path",
        )
    finding = await db.scalar(
        select(ReportFinding).where(
            ReportFinding.call_id == call_id,
            ReportFinding.finding_id == finding_id,
        )
    )
    if finding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    feedback = await db.scalar(
        select(Feedback).where(
            Feedback.call_id == call_id,
            Feedback.finding_id == finding_id,
        )
    )
    if feedback is None:
        feedback = Feedback(
            call_id=call_id,
            workspace_id=workspace_id,
            finding_id=finding_id,
            kind=body.kind,
            verdict=body.verdict,
            comment=body.comment,
        )
        db.add(feedback)
    else:
        feedback.kind = body.kind
        feedback.verdict = body.verdict
        feedback.comment = body.comment
        feedback.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(feedback)
    return serialize(feedback)


@router.delete("/{finding_id}", status_code=204)
async def delete_feedback(
    call_id: UUID,
    finding_id: str,
    workspace_id: Workspace,
    db: Database,
) -> Response:
    await get_call(call_id, workspace_id, db)
    feedback = await db.scalar(
        select(Feedback).where(
            Feedback.call_id == call_id,
            Feedback.finding_id == finding_id,
            Feedback.workspace_id == workspace_id,
        )
    )
    if feedback is not None:
        await db.delete(feedback)
        await db.commit()
    return Response(status_code=204)
