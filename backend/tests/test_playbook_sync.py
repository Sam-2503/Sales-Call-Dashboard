from __future__ import annotations

import json
import shutil
from pathlib import Path

import boto3
import pytest
from call_analyser.config import Settings as PackageSettings
from moto import mock_aws

from analyser_api.config import Settings
from analyser_api.services.playbook_artifact import publish, sync


@pytest.mark.asyncio
async def test_publish_and_sync_round_trip_without_embedding(tmp_path: Path) -> None:
    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket="private-bucket")
        chroma = tmp_path / "chroma"
        chroma.mkdir()
        manifest = chroma / "book_playbook_manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "status": "complete",
                    "pdf_sha256": "abc",
                    "chunker_version": "1",
                    "chunking_parameters": {},
                    "embedding_model": "fake",
                    "embedding_dim": 768,
                    "chunk_count": 2,
                }
            ),
            encoding="utf-8",
        )
        (chroma / "book").mkdir()
        (chroma / "book" / "data.bin").write_bytes(b"chroma")
        settings = Settings(
            _env_file=None,
            storage_backend="s3",
            s3_bucket="private-bucket",
            s3_region="us-east-1",
            playbook_artifact_prefix="playbooks",
            package=PackageSettings(
                _env_file=None,
                chroma_path=chroma,
                embedding_model="fake",
                embedding_dim=768,
                fake_mode=True,
            ),
        )
        key = publish(settings)
        assert key.endswith(".tar.gz")
        assert sync(settings) is False  # local manifest already matches latest
        shutil.rmtree(chroma)
        assert sync(settings) is True
        assert (chroma / "book_playbook_manifest.json").exists()
        assert (chroma / "book" / "data.bin").read_bytes() == b"chroma"
        assert sync(settings) is False
