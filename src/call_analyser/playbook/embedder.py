"""Embedding implementations used by the playbook index."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from call_analyser.config import Settings


def _normalise(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


class FakeEmbeddings(Embeddings):
    """Deterministic hashed bag-of-words embeddings for offline tests."""

    def __init__(self, dimension: int = 768) -> None:
        if dimension < 1:
            raise ValueError("embedding dimension must be positive")
        self.dimension = dimension
        self.document_count = 0
        self.query_count = 0

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            index = int(hashlib.sha256(token.encode()).hexdigest(), 16) % self.dimension
            vector[index] += 1.0
        return _normalise(vector)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_count += len(texts)
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.query_count += 1
        return self._embed(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)


class GeminiEmbeddings(Embeddings):
    """Gemini embeddings with explicit retrieval task types and L2 normalization."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.document_count = 0
        self.query_count = 0
        api_key = SecretStr(self.settings.gemini_api_key) if self.settings.gemini_api_key else None
        self._document_model = GoogleGenerativeAIEmbeddings(
            model=self.settings.embedding_model,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=self.settings.embedding_dim,
            api_key=api_key,
        )
        self._query_model = GoogleGenerativeAIEmbeddings(
            model=self.settings.embedding_model,
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=self.settings.embedding_dim,
            api_key=api_key,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_count += len(texts)
        return [_normalise(vector) for vector in self._document_model.embed_documents(texts)]

    def embed_query(self, text: str) -> list[float]:
        self.query_count += 1
        return _normalise(self._query_model.embed_query(text))

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)
