from pathlib import Path

import pytest
import yaml
from reportlab.pdfgen.canvas import Canvas

from call_analyser.config import Settings
from call_analyser.errors import PlaybookExtractionError
from call_analyser.playbook import chunk_playbook, extract_playbook, load_playbook_spec


def _make_pdf(path: Path, pages: list[str]) -> None:
    canvas = Canvas(str(path))
    for text in pages:
        canvas.drawString(72, 740, "Synthetic Book Header")
        for line_number, line in enumerate(text.splitlines()):
            canvas.drawString(72, 700 - line_number * 18, line)
        canvas.showPage()
    canvas.save()


def _make_spec(tmp_path: Path, pdf: Path) -> Path:
    path = tmp_path / "playbook.yaml"
    path.write_text(yaml.safe_dump({
        "slug": "synthetic",
        "title": "Synthetic Book",
        "author": "Test Author",
        "edition": "1",
        "source_pdf": pdf.name,
        "page_offset": 10,
        "skip_pages": [],
        "language": "en",
    }))
    return path


def test_extract_detects_chapters_and_removes_repeated_headers(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    _make_pdf(
        pdf,
        ["Chapter 1 Discovery\nAsk open questions.", "Chapter 2 Closing\nConfirm next steps."],
    )
    spec = load_playbook_spec(_make_spec(tmp_path, pdf))
    extracted = extract_playbook(spec)
    assert [chapter.title for chapter in extracted.chapters] == [
        "Chapter 1 Discovery",
        "Chapter 2 Closing",
    ]
    assert all(
        "Synthetic Book Header" not in paragraph
        for chapter in extracted.chapters
        for _, paragraph in chapter.paragraphs
    )
    assert extracted.page_count == 2


def test_chunk_ids_are_stable_and_page_offset_is_applied_once(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    _make_pdf(pdf, ["Chapter 1 Discovery\n" + "Ask open questions. " * 100])
    spec = load_playbook_spec(_make_spec(tmp_path, pdf))
    settings = Settings(chunk_target_tokens=40, chunk_max_tokens=60, chunk_overlap_tokens=10)
    extracted = extract_playbook(spec, settings)
    first = chunk_playbook(extracted, spec, settings)
    second = chunk_playbook(extracted, spec, settings)
    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert all(chunk.page_start == 11 for chunk in first)
    assert all(chunk.token_estimate <= 60 for chunk in first)


def test_scanned_style_pdf_is_rejected(tmp_path: Path) -> None:
    pdf = tmp_path / "blank.pdf"
    canvas = Canvas(str(pdf))
    for _ in range(4):
        canvas.showPage()
    canvas.save()
    spec = load_playbook_spec(_make_spec(tmp_path, pdf))
    with pytest.raises(PlaybookExtractionError, match="scanned"):
        extract_playbook(spec)
