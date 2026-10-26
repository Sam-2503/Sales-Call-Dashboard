"""Streaming call upload and workspace-scoped call endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import json
import mimetypes
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from call_analyser.config import Settings as PackageSettings
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select

from analyser_api.auth.tokens import issue_media_token, verify_media_token
from analyser_api.config import Settings
from analyser_api.db.models import Agent, Call, Job
from analyser_api.deps import Database, Storage, Workspace, get_settings
from analyser_api.services.quotas import check_call_quota

router = APIRouter(prefix="/api/v1", tags=["calls"])
MEDIA_TYPES = {
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
    "webm": "audio/webm",
}


async def probe_audio(path: Path, timeout_s: float) -> tuple[float, str]:
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,format_name",
        "-of",
        "json",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout_s)
    except TimeoutError as error:
        process.kill()
        await process.wait()
        raise HTTPException(status_code=422, detail="invalid_audio") from error
    if process.returncode != 0:
        raise HTTPException(status_code=422, detail="invalid_audio")
    try:
        data = json.loads(stdout)
        format_data = data["format"]
        duration = float(format_data["duration"])
        format_name = str(format_data["format_name"]).split(",")[0]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=422, detail="invalid_audio") from error
    return duration, format_name


async def stream_upload(file: UploadFile, limit: int) -> tuple[Path, str, int]:
    digest = hashlib.sha256()
    size = 0
    with tempfile.NamedTemporaryFile(prefix="call-", suffix=".upload", delete=False) as temporary:
        path = Path(temporary.name)
        try:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(status_code=413, detail="file_too_large")
                digest.update(chunk)
                temporary.write(chunk)
        except BaseException:
            path.unlink(missing_ok=True)
            raise
    return path, digest.hexdigest(), size


@router.post("/calls", status_code=202)
async def upload_call(
    db: Database,
    workspace_id: Workspace,
    storage: Storage,
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File(...)],
    consent: Annotated[bool, Form(...)],
    title: Annotated[str | None, Form()] = None,
    agent_id: Annotated[UUID | None, Form()] = None,
) -> dict[str, str]:
    if not consent:
        raise HTTPException(status_code=400, detail="consent_required")
    await check_call_quota(db, workspace_id, settings)
    if agent_id is not None:
        agent = await db.scalar(
            select(Agent).where(Agent.id == agent_id, Agent.workspace_id == workspace_id)
        )
        if agent is None:
            raise HTTPException(status_code=404, detail="Not found")
    path, digest, size = await stream_upload(file, settings.max_upload_mb * 1024 * 1024)
    key: str | None = None
    try:
        duration, format_name = await probe_audio(path, settings.request_timeout_s)
        package_settings = PackageSettings()
        if (
            duration < package_settings.min_duration_s
            or duration > package_settings.max_audio_minutes * 60
        ):
            raise HTTPException(status_code=422, detail="invalid_audio_duration")
        extension = next((ext for ext, mime in MEDIA_TYPES.items() if ext in format_name), "bin")
        call_id = uuid4()
        key = f"{workspace_id}/{call_id}/original.{extension}"
        await storage.put(key, path)
        call = Call(
            id=call_id,
            workspace_id=workspace_id,
            agent_id=agent_id,
            title=title,
            status="queued",
            audio_key=key,
            audio_mime=MEDIA_TYPES.get(extension, mimetypes.types_map.get(f".{extension}")),
            audio_sha256=digest,
            audio_bytes=size,
            duration_s=duration,
            original_filename=Path(file.filename or "recording").name[:255],
            consent_at=datetime.now(UTC),
        )
        db.add(call)
        job = Job(call_id=call_id, status="queued")
        db.add(job)
        await db.commit()
        return {"call_id": str(call_id), "job_id": str(job.id), "status": "queued"}
    except BaseException:
        await db.rollback()
        if key:
            await storage.delete(key)
        raise
    finally:
        path.unlink(missing_ok=True)


@router.get("/calls")
async def list_calls(workspace_id: Workspace, db: Database) -> list[dict[str, object]]:
    result = await db.scalars(
        select(Call).where(Call.workspace_id == workspace_id).order_by(Call.created_at.desc())
    )
    return [
        {
            "id": call.id,
            "title": call.title,
            "status": call.status,
            "created_at": call.created_at,
            "duration_s": call.duration_s,
        }
        for call in result
    ]


@router.get("/calls/{call_id}")
async def get_call(call_id: UUID, workspace_id: Workspace, db: Database) -> dict[str, object]:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": call.id,
        "title": call.title,
        "status": call.status,
        "duration_s": call.duration_s,
    }


@router.delete("/calls/{call_id}", status_code=204)
async def delete_call(
    call_id: UUID, workspace_id: Workspace, db: Database, storage: Storage
) -> None:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None:
        raise HTTPException(status_code=404, detail="Not found")
    if call.audio_key:
        await storage.delete(call.audio_key)
    await db.delete(call)
    await db.commit()
    if call.audio_key:
        await storage.delete(call.audio_key)
    await db.delete(call)
    await db.commit()


@router.get("/calls/{call_id}/audio-url")
async def audio_url(
    call_id: UUID,
    workspace_id: Workspace,
    db: Database,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None or not call.audio_key:
        raise HTTPException(status_code=404, detail="Not found")
    token = issue_media_token(workspace_id, call_id, settings)
    return {"url": f"/api/v1/media/audio?t={token}&call_id={call_id}"}


@router.get("/media/audio")
async def media_audio(
    db: Database,
    storage: Storage,
    settings: Annotated[Settings, Depends(get_settings)],
    token: Annotated[str, Query(alias="t")],
    call_id: Annotated[UUID, Query(...)],
    range_header: Annotated[str | None, Header(alias="Range")] = None,
) -> Response:
    try:
        workspace_id = verify_media_token(token, call_id, settings)
    except Exception as error:
        raise HTTPException(status_code=401, detail="unauthorized") from error
    call = await db.scalar(
        select(Call).where(Call.id == call_id, Call.workspace_id == workspace_id)
    )
    if call is None or not call.audio_key:
        raise HTTPException(status_code=404, detail="Not found")
    total = await storage.size(call.audio_key)
    start, end = 0, total - 1
    if range_header:
        if not range_header.startswith("bytes="):
            raise HTTPException(status_code=416, detail="invalid_range")
        value = range_header[6:].split(",", 1)[0]
        left, _, right = value.partition("-")
        try:
            if left:
                start = int(left)
                end = int(right) if right else total - 1
            else:
                suffix = int(right)
                start = max(0, total - suffix)
            if start < 0 or end >= total or start > end:
                raise ValueError
        except ValueError as error:
            raise HTTPException(status_code=416, detail="invalid_range") from error
    body = await storage.open_range(call.audio_key, start, end)
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(body)),
        "Cache-Control": "private, no-store",
    }
    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
    return Response(
        content=body,
        status_code=206 if range_header else 200,
        media_type=call.audio_mime or "application/octet-stream",
        headers=headers,
    )
