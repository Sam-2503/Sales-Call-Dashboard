"""Score-preserving retrieval from the read-only playbook index."""

from __future__ import annotations

import asyncio

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field

from playbook.index import ReadOnlyPlaybookIndex


def strip_embedding_header(text: str) -> str:
    """Remove the stored ``title | chapter`` line before showing passage text."""
    return text.split("\n", 1)[1] if "\n" in text else text


class PlaybookRetriever(BaseRetriever):
    """Thin retriever that preserves passage IDs and relevance scores."""

    index: ReadOnlyPlaybookIndex = Field(exclude=True)
    top_k: int = 4
    min_score: float = 0.0
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def _get_relevant_documents(self, query: str, *, run_manager: object) -> list[Document]:
        results = self.index.search(query, self.top_k)
        documents: list[Document] = []
        for document, score in results:
            if score < self.min_score:
                continue
            metadata = dict(document.metadata)
            passage_id = metadata.pop("id", metadata.get("passage_id", ""))
            metadata.update(passage_id=passage_id, score=score)
            documents.append(
                Document(
                    page_content=strip_embedding_header(document.page_content),
                    metadata=metadata,
                )
            )
        return documents

    async def _aget_relevant_documents(self, query: str, *, run_manager: object) -> list[Document]:
        return await asyncio.to_thread(self._get_relevant_documents, query, run_manager=run_manager)
