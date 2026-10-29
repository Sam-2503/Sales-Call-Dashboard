import json
from pathlib import Path

import pytest
from call_analyser.config import Settings as PackageSettings

from analyser_api.config import Settings
from analyser_api.services.playbook_artifact import publish


def test_publish_refuses_incomplete_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "book_playbook_manifest.json"
    manifest.write_text(json.dumps({"status": "building"}), encoding="utf-8")
    settings = Settings(
        _env_file=None,
        storage_backend="s3",
        s3_bucket="private-bucket",
        playbook_artifact_prefix="playbooks",
        package=PackageSettings(_env_file=None, chroma_path=tmp_path),
    )
    with pytest.raises(RuntimeError, match="not complete"):
        publish(settings)


def test_publish_requires_exactly_one_manifest(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        storage_backend="s3",
        s3_bucket="private-bucket",
        playbook_artifact_prefix="playbooks",
        package=PackageSettings(_env_file=None, chroma_path=tmp_path),
    )
    with pytest.raises(RuntimeError, match="exactly one"):
        publish(settings)
