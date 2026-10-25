from pathlib import Path

import yaml
from reportlab.pdfgen.canvas import Canvas

from config import Settings
from playbook import index_playbook, load_playbook_spec, open_playbook
from playbook.retriever import PlaybookRetriever


def _indexed_playbook(tmp_path: Path) -> tuple[PlaybookRetriever, Settings]:
    pdf = tmp_path / "book.pdf"
    canvas = Canvas(str(pdf))
    canvas.drawString(72, 700, "Chapter 1 Discovery")
    canvas.drawString(72, 680, "Discovery questions reveal workflow problems and business impact.")
    canvas.showPage()
    canvas.drawString(72, 700, "Chapter 2 Closing")
    canvas.drawString(72, 680, "Closing commitments confirm the next meeting and owner.")
    canvas.showPage()
    canvas.save()
    spec_path = tmp_path / "playbook.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "slug": "retrieval",
                "title": "Synthetic Retrieval",
                "author": "Tester",
                "edition": "1",
                "source_pdf": "book.pdf",
            }
        )
    )
    settings = Settings(
        fake_mode=True,
        chroma_path=tmp_path / "chroma",
        chunk_target_tokens=8,
        chunk_max_tokens=12,
        chunk_overlap_tokens=0,
    )
    spec = load_playbook_spec(spec_path)
    index_playbook(spec, settings)
    return PlaybookRetriever(index=open_playbook(spec, settings), top_k=2, min_score=0), settings


def test_retriever_returns_id_metadata_and_strips_embedding_header(tmp_path: Path) -> None:
    retriever, _ = _indexed_playbook(tmp_path)
    documents = retriever.invoke("workflow problems business impact")
    assert documents
    assert documents[0].metadata["passage_id"]
    assert documents[0].metadata["score"] >= 0
    assert "Synthetic Retrieval |" not in documents[0].page_content


def test_retriever_min_score_filters_results(tmp_path: Path) -> None:
    retriever, _ = _indexed_playbook(tmp_path)
    retriever.min_score = 1.1
    assert retriever.invoke("workflow problems") == []
