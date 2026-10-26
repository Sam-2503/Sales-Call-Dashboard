"""Workspace and agent API contracts."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

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


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AgentUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AgentResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
