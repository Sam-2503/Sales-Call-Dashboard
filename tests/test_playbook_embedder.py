import math

import pytest

from call_analyser.playbook.embedder import FakeEmbeddings


def _norm(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


@pytest.mark.asyncio
async def test_fake_embeddings_are_deterministic_normalized_and_counted() -> None:
    embeddings = FakeEmbeddings(dimension=32)

    first = embeddings.embed_documents(["Discovery questions reveal impact"])
    second = embeddings.embed_documents(["Discovery questions reveal impact"])
    query = embeddings.embed_query("discovery impact")

    assert first == second
    assert len(first[0]) == 32
    assert _norm(first[0]) == pytest.approx(1)
    assert _norm(query) == pytest.approx(1)
    assert embeddings.document_count == 2
    assert embeddings.query_count == 1


@pytest.mark.asyncio
async def test_fake_embeddings_async_methods_match_sync_methods() -> None:
    embeddings = FakeEmbeddings(dimension=16)

    documents = await embeddings.aembed_documents(["same text", ""])
    query = await embeddings.aembed_query("")

    assert documents[0] == embeddings.embed_documents(["same text"])[0]
    assert documents[1] == [0.0] * 16
    assert query == [0.0] * 16
