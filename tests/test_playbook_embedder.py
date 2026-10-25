import math

import pytest

from playbook.embedder import FakeEmbeddings


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


def test_fake_embeddings_use_bounded_query_cache() -> None:
    embeddings = FakeEmbeddings(dimension=8, cache_size=1)

    first = embeddings.embed_query("first")
    cached = embeddings.embed_query("first")
    embeddings.embed_query("second")
    evicted = embeddings.embed_query("first")

    assert first == cached == evicted
    assert embeddings.query_count == 3


def test_fake_embeddings_return_defensive_cache_copies() -> None:
    embeddings = FakeEmbeddings(dimension=8, cache_size=1)

    first = embeddings.embed_query("same")
    first[0] = 99

    assert embeddings.embed_query("same") != first
    assert embeddings.query_count == 1


def test_fake_embeddings_cache_zero_disables_reuse() -> None:
    embeddings = FakeEmbeddings(dimension=8, cache_size=0)

    embeddings.embed_query("same")
    embeddings.embed_query("same")

    assert embeddings.query_count == 2


def test_fake_embeddings_reject_negative_cache_size() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        FakeEmbeddings(dimension=8, cache_size=-1)


def test_fake_embeddings_cache_uses_recently_used_order() -> None:
    embeddings = FakeEmbeddings(dimension=8, cache_size=2)

    embeddings.embed_query("first")
    embeddings.embed_query("second")
    embeddings.embed_query("first")
    embeddings.embed_query("third")
    embeddings.embed_query("second")

    assert embeddings.query_count == 4
