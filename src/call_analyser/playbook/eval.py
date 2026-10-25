"""Offline retrieval evaluation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from call_analyser.errors import PlaybookExtractionError
from call_analyser.playbook.retriever import PlaybookRetriever


def _relevant(document: Any, references: list[str]) -> bool:
    chapter = str(document.metadata.get("chapter", "")).lower()
    page = int(document.metadata.get("page_start", 0))
    return any(
        reference.lower() in chapter
        or (
            "-" in reference
            and int(reference.split("-", 1)[0]) <= page <= int(reference.split("-", 1)[1])
        )
        or (reference.isdigit() and int(reference) == page)
        for reference in references
    )


def load_queries(path: str | Path) -> list[dict[str, Any]]:
    """Load retrieval queries with text and relevant chapter/page references."""
    try:
        raw = yaml.safe_load(Path(path).read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise PlaybookExtractionError(f"could not read retrieval queries: {error}") from error
    if not isinstance(raw, list):
        raise PlaybookExtractionError("retrieval queries must be a YAML list")
    return raw


def evaluate_retrieval(
    retriever: PlaybookRetriever, queries: list[dict[str, Any]]
) -> dict[str, float | int | str]:
    """Compute hit@1/3/5, MRR and sample count without network calls."""
    if not queries:
        return {"reason": "no queries provided", "n": 0}
    hits = {1: 0, 3: 0, 5: 0}
    reciprocal_ranks: list[float] = []
    for query in queries:
        references = [str(value) for value in query.get("relevant", [])]
        documents = retriever.invoke(str(query["text"]))
        ranks = [
            index
            for index, document in enumerate(documents, 1)
            if _relevant(document, references)
        ]
        if ranks:
            first = ranks[0]
            reciprocal_ranks.append(1 / first)
            for cutoff in hits:
                hits[cutoff] += first <= cutoff
        else:
            reciprocal_ranks.append(0.0)
    count = len(queries)
    return {
        "hit@1": hits[1] / count,
        "hit@3": hits[3] / count,
        "hit@5": hits[5] / count,
        "mrr": sum(reciprocal_ranks) / count,
        "n": count,
    }
