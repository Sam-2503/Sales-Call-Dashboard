"""Deterministic PDF extraction and chapter detection."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

from pypdf import PdfReader

from config import Settings
from errors import PlaybookExtractionError
from playbook.spec import PlaybookSpec


@dataclass(frozen=True)
class ExtractedPage:
    number: int
    printed_number: int
    text: str


@dataclass(frozen=True)
class ChapterText:
    title: str
    start_page: int
    end_page: int
    paragraphs: list[tuple[int, str]]


@dataclass(frozen=True)
class ExtractedPlaybook:
    pdf_sha256: str
    page_count: int
    skipped_pages: list[int]
    empty_pages: list[int]
    chapters: list[ChapterText]


def _clean_page(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).replace("\r", "\n")
    normalized = re.sub(r"[\u25a0\u2022\u00a7]", "\n", normalized)
    normalized = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", normalized)
    lines = [re.sub(r"\s+", " ", line).strip() for line in normalized.splitlines()]
    lines = [line for line in lines if line and not re.fullmatch(r"\d+", line)]
    paragraphs: list[str] = []
    current: list[str] = []
    chapter_heading = re.compile(r"^(?:chapter|part)\s+[0-9ivxlcdm]+", re.I)
    for line in lines:
        if current and (
            current[-1].endswith((".", "!", "?"))
            or chapter_heading.match(current[0]) and not chapter_heading.match(line)
        ):
            paragraphs.append(" ".join(current))
            current = []
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def _remove_running_lines(texts: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    for text in texts:
        lines = {line.strip() for line in text.splitlines() if line.strip()}
        for line in lines:
            counts[line] = counts.get(line, 0) + 1
    threshold = max(2, int(len(texts) * 0.3 + 0.999))
    repeated = {line for line, count in counts.items() if count >= threshold}
    return [
        "\n".join(line for line in text.splitlines() if line.strip() not in repeated)
        for text in texts
    ]


def _heuristic_chapters(pages: list[ExtractedPage]) -> list[tuple[str, int, int]]:
    markers: list[tuple[str, int]] = []
    pattern = re.compile(r"^\s*((?:chapter|part)\s+[0-9ivxlcdm]+[^\n]*)$", re.I)
    for page in pages:
        for line in page.text.splitlines():
            match = pattern.match(line)
            if match:
                markers.append((match.group(1).strip(), page.number))
                break
    if not markers:
        return [("Unknown", pages[0].number, pages[-1].number)] if pages else []
    result = []
    for index, (title, start) in enumerate(markers):
        end = markers[index + 1][1] - 1 if index + 1 < len(markers) else pages[-1].number
        result.append((title, start, end))
    return result


def extract_playbook(spec: PlaybookSpec, settings: Settings | None = None) -> ExtractedPlaybook:
    """Extract text page-by-page and assign every included page to one chapter."""
    settings = settings or Settings()
    try:
        pdf_bytes = spec.source_pdf.read_bytes()
        reader = PdfReader(spec.source_pdf)
    except (OSError, ValueError) as error:
        raise PlaybookExtractionError(f"could not read playbook PDF: {error}") from error
    raw_texts = [(page.extract_text() or "") for page in reader.pages]
    cleaned = _remove_running_lines(raw_texts)
    skipped = spec.skip_page_numbers()
    pages = [
        ExtractedPage(index, index + spec.page_offset, _clean_page(text))
        for index, text in enumerate(cleaned, 1)
        if index not in skipped
    ]
    empty = [page.number for page in pages if not page.text.strip()]
    if pages and len(empty) / len(pages) > settings.playbook_max_empty_page_ratio:
        raise PlaybookExtractionError(
            "the PDF looks scanned because too many pages have no extractable text; "
            "OCR is out of scope"
        )
    if not pages:
        raise PlaybookExtractionError("playbook contains no non-skipped pages")
    if spec.chapters:
        ranges = [
            (chapter.title, chapter.start_page, chapter.end_page)
            for chapter in spec.chapters
        ]
    else:
        ranges = _heuristic_chapters(pages)
    chapters: list[ChapterText] = []
    for title, start, end in ranges:
        included = [
            (page.printed_number, paragraph)
            for page in pages
            if start <= page.number <= end
            for paragraph in page.text.split("\n\n")
        ]
        chapters.append(ChapterText(title, start, end, included))
    return ExtractedPlaybook(
        hashlib.sha256(pdf_bytes).hexdigest(),
        len(reader.pages),
        sorted(skipped),
        empty,
        chapters,
    )
