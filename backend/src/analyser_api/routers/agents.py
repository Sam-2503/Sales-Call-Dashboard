"""Workspace-scoped agent endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from analyser_api.db.models import Agent
from analyser_api.deps import Database, Workspace
from analyser_api.schemas.api import AgentCreate, AgentResponse, AgentUpdate

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


def serialize(agent: Agent) -> AgentResponse:
    return AgentResponse(id=agent.id, name=agent.name, created_at=agent.created_at)


@router.get("", response_model=list[AgentResponse])
async def list_agents(workspace_id: Workspace, db: Database) -> list[AgentResponse]:
    result = await db.scalars(
        select(Agent).where(Agent.workspace_id == workspace_id).order_by(Agent.created_at)
    )
    return [serialize(agent) for agent in result]


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(workspace_id: Workspace, body: AgentCreate, db: Database) -> AgentResponse:
    agent = Agent(workspace_id=workspace_id, name=body.name)
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return serialize(agent)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    workspace_id: Workspace, agent_id: UUID, body: AgentUpdate, db: Database
) -> AgentResponse:
    agent = await db.scalar(
        select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    agent.name = body.name
    await db.commit()
    await db.refresh(agent)
    return serialize(agent)
