"""Embedding implementations used by the playbook index."""

from __future__ import annotations

import asyncio
import hashlib
import math
import re
from collections import OrderedDict
from threading import Lock

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pydantic import SecretStr

from call_analyser.config import Settings


def _normalise(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


class _QueryEmbeddingCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        self._values: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = Lock()

    def get(self, query: str) -> list[float] | None:
        if not self.max_size:
            return None
        with self._lock:
            value = self._values.get(query)
            if value is None:
                return None
            self._values.move_to_end(query)
            return value.copy()

    def put(self, query: str, vector: list[float]) -> None:
        if not self.max_size:
            return
        with self._lock:
            self._values[query] = vector.copy()
            self._values.move_to_end(query)
            while len(self._values) > self.max_size:
                self._values.popitem(last=False)


class FakeEmbeddings(Embeddings):
    """Deterministic hashed bag-of-words embeddings for offline tests."""

    def __init__(self, dimension: int = 768, cache_size: int = 0) -> None:
        if dimension < 1:
            raise ValueError("embedding dimension must be positive")
        if cache_size < 0:
            raise ValueError("embedding cache size must be non-negative")
        self.dimension = dimension
        self.cache_size = cache_size
        self.document_count = 0
        self.query_count = 0
        self._query_cache = _QueryEmbeddingCache(cache_size)

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
        cached = self._query_cache.get(text)
        if cached is not None:
            return cached
        self.query_count += 1
        vector = self._embed(text)
        self._query_cache.put(text, vector)
        return vector

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
        self._query_cache = _QueryEmbeddingCache(self.settings.query_embed_cache_size)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.document_count += len(texts)
        return [_normalise(vector) for vector in self._document_model.embed_documents(texts)]

    def embed_query(self, text: str) -> list[float]:
        cached = self._query_cache.get(text)
        if cached is not None:
            return cached
        self.query_count += 1
        vector = _normalise(self._query_model.embed_query(text))
        self._query_cache.put(text, vector)
        return vector

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query, text)
