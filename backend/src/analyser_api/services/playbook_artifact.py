"""Publish and restore the private playbook index artifact without embedding."""

from __future__ import annotations

import hashlib
import json
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import boto3
from call_analyser.config import Settings as PackageSettings
from call_analyser.playbook import PlaybookIndex, load_playbook_spec

from analyser_api.config import Settings


def _client(settings: Settings) -> Any:
    if settings.storage_backend != "s3" or not settings.s3_bucket:
        raise RuntimeError("S3 storage must be configured for playbook artifacts")
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
    )


def _prefix(settings: Settings) -> str:
    if not settings.playbook_artifact_prefix:
        raise RuntimeError("PLAYBOOK_ARTIFACT_PREFIX is not configured")
    return settings.playbook_artifact_prefix.rstrip("/")


def _manifest(settings: Settings) -> tuple[Path, dict[str, Any]]:
    candidates = list(settings.package.chroma_path.glob("*_playbook_manifest.json"))
    if len(candidates) != 1:
        raise RuntimeError("exactly one playbook manifest is required")
    path = candidates[0]
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "complete":
        raise RuntimeError("playbook index is not complete")
    return path, data


def _summary(manifest: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "pdf_sha256",
        "chunker_version",
        "chunking_parameters",
        "embedding_model",
        "embedding_dim",
        "chunk_count",
    )
    return {key: manifest.get(key) for key in keys}


def publish(settings: Settings) -> str:
    manifest_path, manifest = _manifest(settings)
    client = _client(settings)
    prefix = _prefix(settings)
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temporary:
        archive_path = Path(temporary.name)
    try:
        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(settings.package.chroma_path, arcname="chroma")
            archive.add(manifest_path, arcname=f"chroma/{manifest_path.name}")
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        key = f"{prefix}/{uuid4().hex}-{digest}.tar.gz"
        client.upload_file(str(archive_path), settings.s3_bucket, key)
        latest = {"file": key, "sha256": digest, "manifest": _summary(manifest)}
        client.put_object(
            Bucket=settings.s3_bucket,
            Key=f"{prefix}/latest.json",
            Body=json.dumps(latest, sort_keys=True).encode(),
            ContentType="application/json",
        )
        return key
    finally:
        archive_path.unlink(missing_ok=True)


def _download(client: Any, settings: Settings, key: str) -> bytes:
    response = client.get_object(Bucket=settings.s3_bucket, Key=key)
    return bytes(response["Body"].read())


def sync(settings: Settings) -> bool:
    """Return True when an artifact was installed; never index or embed."""
    if not settings.playbook_artifact_prefix:
        return False
    client = _client(settings)
    prefix = _prefix(settings)
    latest = json.loads(_download(client, settings, f"{prefix}/latest.json"))
    local_paths = list(settings.package.chroma_path.glob("*_playbook_manifest.json"))
    if len(local_paths) == 1:
        local = json.loads(local_paths[0].read_text(encoding="utf-8"))
        if _summary(local) == latest.get("manifest"):
            return False
    payload = _download(client, settings, latest["file"])
    if hashlib.sha256(payload).hexdigest() != latest["sha256"]:
        raise RuntimeError("playbook artifact checksum mismatch")
    target = settings.package.chroma_path
    staging = target.with_name(f"{target.name}.staging-{uuid4().hex}")
    backup = target.with_name(f"{target.name}.backup-{uuid4().hex}")
    staging.mkdir(parents=True)
    archive_path = staging / "artifact.tar.gz"
    archive_path.write_bytes(payload)
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(staging, filter="data")
        extracted = staging / "chroma"
        if not extracted.is_dir():
            raise RuntimeError("artifact has no chroma directory")
        if target.exists():
            target.rename(backup)
        extracted.rename(target)
        if settings.playbook_path:
            PlaybookIndex.open(
                load_playbook_spec(settings.playbook_path),
                PackageSettings().model_copy(update={"chroma_path": target}),
            )
        if backup.exists():
            shutil.rmtree(backup, ignore_errors=True)
        return True
    except Exception:
        if backup.exists():
            if target.exists():
                shutil.rmtree(target)
            backup.rename(target)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
