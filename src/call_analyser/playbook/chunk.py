"""Deterministic chapter-local playbook chunking."""

from __future__ import annotations

import hashlib
import re

from call_analyser.config import Settings
from call_analyser.playbook.extract import ChapterText, ExtractedPlaybook
from call_analyser.playbook.spec import PlaybookSpec
from call_analyser.schemas.playbook import PlaybookChunk

CHUNKER_VERSION = "1"


def _estimate(text: str, factor: float) -> int:
    return max(1, round(len(text.split()) * factor))


def _split_paragraph(text: str, max_tokens: int, factor: float) -> list[str]:
    if _estimate(text, factor) <= max_tokens:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    pieces: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        if current and _estimate(" ".join(current + [sentence]), factor) > max_tokens:
            pieces.append(" ".join(current))
            current = []
        current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    if any(_estimate(piece, factor) > max_tokens for piece in pieces):
        words = text.split()
        words_per_piece = max(1, int(max_tokens / factor))
        pieces = [
            " ".join(words[index : index + words_per_piece])
            for index in range(0, len(words), words_per_piece)
        ]
    return pieces


def _chapter_chunks(
    chapter: ChapterText, spec: PlaybookSpec, settings: Settings, pdf_sha256: str
) -> list[PlaybookChunk]:
    paragraphs: list[tuple[int, str]] = []
    for page, text in chapter.paragraphs:
        paragraphs.extend(
            (page, piece)
            for piece in _split_paragraph(
                text, settings.chunk_max_tokens, settings.token_estimate_factor
            )
        )
    chunks: list[PlaybookChunk] = []
    start = 0
    ordinal = 0
    while start < len(paragraphs):
        selected: list[tuple[int, str]] = []
        index = start
        while index < len(paragraphs):
            candidate = selected + [paragraphs[index]]
            candidate_text = " ".join(text for _, text in candidate)
            if (
                selected
                and _estimate(candidate_text, settings.token_estimate_factor)
                > settings.chunk_target_tokens
            ):
                break
            selected = candidate
            index += 1
            selected_text = " ".join(text for _, text in selected)
            if (
                _estimate(selected_text, settings.token_estimate_factor)
                >= settings.chunk_target_tokens
            ):
                break
        if not selected:
            selected = [paragraphs[start]]
            index = start + 1
        text = "\n\n".join(text for _, text in selected)
        digest = hashlib.sha1(text.encode()).hexdigest()
        chunk_id = hashlib.sha1(
            f"{pdf_sha256}|{CHUNKER_VERSION}|{chapter.title}|{ordinal}|{digest}".encode()
        ).hexdigest()[:16]
        embedding_text = f"{spec.title} | {chapter.title}\n{text}"
        chunks.append(
            PlaybookChunk(
                id=chunk_id,
                text=text,
                embedding_text=embedding_text,
                book_slug=spec.slug,
                chapter=chapter.title,
                page_start=min(page for page, _ in selected),
                page_end=max(page for page, _ in selected),
                ordinal=ordinal,
                token_estimate=_estimate(text, settings.token_estimate_factor),
            )
        )
        ordinal += 1
        if index >= len(paragraphs):
            break
        overlap_count = 0
        overlap_tokens = 0
        for paragraph_index in range(index - 1, start - 1, -1):
            paragraph_tokens = _estimate(
                paragraphs[paragraph_index][1], settings.token_estimate_factor
            )
            if overlap_tokens + paragraph_tokens > settings.chunk_overlap_tokens:
                break
            overlap_tokens += paragraph_tokens
            overlap_count += 1
        start = max(start + 1, index - overlap_count)
    return chunks


def chunk_playbook(
    extracted: ExtractedPlaybook, spec: PlaybookSpec, settings: Settings | None = None
) -> list[PlaybookChunk]:
    """Chunk each chapter independently with deterministic IDs."""
    settings = settings or Settings()
    return [
        chunk
        for chapter in extracted.chapters
        for chunk in _chapter_chunks(chapter, spec, settings, extracted.pdf_sha256)
    ]
