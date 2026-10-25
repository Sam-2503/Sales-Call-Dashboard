"""Persistent Chroma indexing and read-only playbook access."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from langchain_chroma import Chroma
from langchain_core.documents import Document

from call_analyser.config import Settings
from call_analyser.errors import PlaybookIndexMismatchError, PlaybookNotIndexedError
from call_analyser.playbook.chunk import CHUNKER_VERSION, chunk_playbook
from call_analyser.playbook.embedder import FakeEmbeddings, GeminiEmbeddings
from call_analyser.playbook.extract import extract_playbook
from call_analyser.playbook.spec import PlaybookSpec


def manifest_path(spec: PlaybookSpec, settings: Settings) -> Path:
    return settings.chroma_path / f"{spec.slug}_{settings.embedding_manifest_name}"


def _parameters(settings: Settings) -> dict[str, Any]:
    return {
        "chunk_target_tokens": settings.chunk_target_tokens,
        "chunk_max_tokens": settings.chunk_max_tokens,
        "chunk_overlap_tokens": settings.chunk_overlap_tokens,
        "token_estimate_factor": settings.token_estimate_factor,
    }


def _read_manifest(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return cast(dict[str, Any], json.loads(path.read_text()))
    except (OSError, json.JSONDecodeError) as error:
        raise PlaybookIndexMismatchError(f"invalid playbook manifest {path}: {error}") from error


def _write_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _embedding(settings: Settings) -> FakeEmbeddings | GeminiEmbeddings:
    return (
        FakeEmbeddings(settings.embedding_dim, settings.query_embed_cache_size)
        if settings.fake_mode
        else GeminiEmbeddings(settings)
    )


def _store(spec: PlaybookSpec, settings: Settings, embedding: Any) -> Chroma:
    return Chroma(
        collection_name=f"playbook_{spec.slug}",
        embedding_function=embedding,
        persist_directory=str(settings.chroma_path / spec.slug),
        collection_metadata={"hnsw:space": "cosine"},
    )


def _manifest_matches(manifest: dict[str, Any], extracted_hash: str, settings: Settings) -> bool:
    return (
        manifest.get("status") == "complete"
        and manifest.get("pdf_sha256") == extracted_hash
        and manifest.get("chunker_version") == CHUNKER_VERSION
        and manifest.get("chunking_parameters") == _parameters(settings)
        and manifest.get("embedding_model") == settings.embedding_model
        and manifest.get("embedding_dim") == settings.embedding_dim
    )


def index_playbook(
    spec: PlaybookSpec,
    settings: Settings | None = None,
    *,
    rebuild: bool = False,
    yes: bool = False,
) -> dict[str, Any]:
    """Build or resume an index, embedding only missing deterministic chunk IDs."""
    settings = settings or Settings()
    extracted = extract_playbook(spec, settings)
    chunks = chunk_playbook(extracted, spec, settings)
    path = manifest_path(spec, settings)
    existing = _read_manifest(path)
    if existing and _manifest_matches(existing, extracted.pdf_sha256, settings):
        return existing
    if existing and not rebuild:
        raise PlaybookIndexMismatchError(
            "playbook index settings or source changed; rerun with "
            f"--rebuild --yes or inspect {path}"
        )
    if rebuild and not yes:
        raise PlaybookIndexMismatchError("rebuild requires --yes confirmation")
    embedding = _embedding(settings)
    if rebuild:
        shutil.rmtree(settings.chroma_path / spec.slug, ignore_errors=True)
    store = _store(spec, settings, embedding)
    present = set(store.get(include=[]).get("ids", []))
    payload: dict[str, Any] = {
        "manifest_schema_version": 1,
        "status": "building",
        "slug": spec.slug,
        "title": spec.title,
        "author": spec.author,
        "edition": spec.edition,
        "pdf_sha256": extracted.pdf_sha256,
        "page_count": extracted.page_count,
        "pages_indexed": extracted.page_count - len(extracted.skipped_pages),
        "chunker_version": CHUNKER_VERSION,
        "chunking_parameters": _parameters(settings),
        "embedding_model": settings.embedding_model,
        "embedding_dim": settings.embedding_dim,
        "expected_chunk_count": len(chunks),
        "actual_chunk_count": len(present),
        "estimated_embedded_tokens": sum(chunk.token_estimate for chunk in chunks),
        "pipeline_version": settings.pipeline_version,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _write_manifest(path, payload)
    for offset in range(0, len(chunks), settings.embed_batch_size):
        batch = [
            chunk
            for chunk in chunks[offset : offset + settings.embed_batch_size]
            if chunk.id not in present
        ]
        if not batch:
            continue
        store.add_documents(
            [
                Document(
                    page_content=chunk.embedding_text,
                    metadata={
                        "book_slug": chunk.book_slug,
                        "passage_id": chunk.id,
                        "chapter": chunk.chapter,
                        "page_start": chunk.page_start,
                        "page_end": chunk.page_end,
                        "ordinal": chunk.ordinal,
                        "chunker_version": CHUNKER_VERSION,
                    },
                )
                for chunk in batch
            ],
            ids=[chunk.id for chunk in batch],
        )
        present.update(chunk.id for chunk in batch)
    if len(present) != len(chunks):
        raise PlaybookIndexMismatchError(
            f"index incomplete: expected {len(chunks)} chunks, found {len(present)}"
        )
    payload.update(
        status="complete",
        actual_chunk_count=len(present),
        completed_at=datetime.now(UTC).isoformat(),
    )
    _write_manifest(path, payload)
    return payload


class ReadOnlyPlaybookIndex:
    """Read-only facade intentionally exposing no Chroma write methods."""

    def __init__(self, store: Chroma, manifest: dict[str, Any]) -> None:
        self._store = store
        self.manifest = manifest

    def count(self) -> int:
        return len(self._store.get(include=[]).get("ids", []))

    def search(self, query: str, k: int) -> list[tuple[Document, float]]:
        return self._store.similarity_search_with_relevance_scores(query, k=k)


def open_playbook(spec: PlaybookSpec, settings: Settings | None = None) -> ReadOnlyPlaybookIndex:
    """Open a complete, matching index without reading the source PDF."""
    settings = settings or Settings()
    path = manifest_path(spec, settings)
    manifest = _read_manifest(path)
    if manifest is None or manifest.get("status") != "complete":
        raise PlaybookNotIndexedError(
            f"playbook is not indexed; run `call-analyser playbook index {spec.slug}`"
        )
    if (
        manifest.get("embedding_model") != settings.embedding_model
        or manifest.get("embedding_dim") != settings.embedding_dim
    ):
        raise PlaybookIndexMismatchError(
            f"playbook index does not match settings; run `call-analyser playbook index "
            f"{spec.slug} --rebuild --yes`"
        )
    return ReadOnlyPlaybookIndex(_store(spec, settings, _embedding(settings)), manifest)


class PlaybookIndex:
    """Public index API; writes are available only through the explicit index command."""

    @staticmethod
    def open(
        spec: PlaybookSpec, settings: Settings | None = None
    ) -> ReadOnlyPlaybookIndex:
        return open_playbook(spec, settings)
