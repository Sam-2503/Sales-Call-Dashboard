from pathlib import Path

import yaml
from reportlab.pdfgen.canvas import Canvas

from config import Settings
from playbook import index_playbook, load_playbook_spec, open_playbook
from playbook.embedder import FakeEmbeddings


def _fixture(tmp_path: Path) -> tuple[Path, Settings]:
    pdf = tmp_path / "book.pdf"
    canvas = Canvas(str(pdf))
    canvas.drawString(72, 700, "Chapter 1 Discovery")
    canvas.drawString(72, 680, "Ask open questions about the current process.")
    canvas.showPage()
    canvas.save()
    spec_path = tmp_path / "playbook.yaml"
    spec_path.write_text(yaml.safe_dump({
        "slug": "synthetic",
        "title": "Synthetic",
        "author": "Tester",
        "edition": "1",
        "source_pdf": "book.pdf",
    }))
    settings = Settings(
        fake_mode=True,
        chroma_path=tmp_path / "chroma",
        chunk_target_tokens=20,
        chunk_max_tokens=30,
        chunk_overlap_tokens=0,
    )
    return spec_path, settings


def test_index_is_idempotent_and_read_only_open_does_not_embed_documents(
    tmp_path: Path,
) -> None:
    spec_path, settings = _fixture(tmp_path)
    spec = load_playbook_spec(spec_path)
    first = index_playbook(spec, settings)
    assert first["status"] == "complete"
    second = index_playbook(spec, settings)
    assert second["status"] == "complete"
    opened = open_playbook(spec, settings)
    assert opened.count() == first["expected_chunk_count"]
    assert not hasattr(opened, "add_documents")


def test_open_missing_index_fails_with_remediation(tmp_path: Path) -> None:
    from errors import PlaybookNotIndexedError

    spec_path, settings = _fixture(tmp_path)
    spec = load_playbook_spec(spec_path)
    try:
        open_playbook(spec, settings)
    except PlaybookNotIndexedError as error:
        assert "playbook index" in str(error)
    else:
        raise AssertionError("expected missing-index failure")


def test_fake_embeddings_reject_non_positive_dimensions() -> None:
    try:
        FakeEmbeddings(0)
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("expected invalid dimension failure")
