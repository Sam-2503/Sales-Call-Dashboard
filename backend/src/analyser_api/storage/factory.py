"""Construct the configured audio storage backend."""

from __future__ import annotations

from analyser_api.config import Settings
from analyser_api.storage.base import AudioStorage
from analyser_api.storage.local import LocalStorage
from analyser_api.storage.s3 import S3Storage


def create_storage(settings: Settings) -> AudioStorage:
    if settings.storage_backend == "local":
        return LocalStorage(settings.storage_dir)
    if not settings.s3_bucket:
        raise ValueError("S3_BUCKET is required when STORAGE_BACKEND=s3")
    return S3Storage(
        settings.s3_bucket,
        settings.s3_endpoint_url,
        settings.s3_region,
        settings.s3_access_key_id,
        settings.s3_secret_access_key,
    )
