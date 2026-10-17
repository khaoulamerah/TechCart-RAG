from __future__ import annotations

from typing import Any

from backend.rag.retriever.retriever import Retriever
from backend.rag.reranker.base import Reranker


class FakeEmbedder:
    model = "fake-embedding-model"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class FakeVectorStore:
    def __init__(self) -> None:
        self.documents = [
            {"id": "gpu", "score": 0.8, "payload": {"text": "GPU specs"}},
            {"id": "return", "score": 0.7, "payload": {"text": "Return policy"}},
            {"id": "shipping", "score": 0.6, "payload": {"text": "Shipping terms"}},
        ]

    def search(self, query_vector: list[float], limit: int) -> list[dict[str, Any]]:
        assert query_vector == [0.1, 0.2, 0.3]
        return self.documents[:limit]


class FakeReranker(Reranker):
    model_name = "fake-reranker"

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        scores = {"gpu": 0.1, "return": 0.95, "shipping": 0.55}
        ranked = [
            {**doc, "rerank_score": scores[str(doc["id"])]}
            for doc in documents
        ]
        return sorted(ranked, key=lambda item: item["rerank_score"], reverse=True)[:top_k]


def test_retriever_reranks_candidates_and_records_trace() -> None:
    retriever = Retriever(
        embedder=FakeEmbedder(),  # type: ignore[arg-type]
        vector_store=FakeVectorStore(),  # type: ignore[arg-type]
        reranker=FakeReranker(),
        retrieval_k=3,
        top_k=2,
    )

    documents, trace = retriever.retrieve_with_trace("What is the return policy?")

    assert [doc["id"] for doc in documents] == ["return", "shipping"]
    assert trace["retrieval"]["top_k"] == 3
    assert trace["reranking"]["model"] == "fake-reranker"
    assert trace["reranking"]["input_count"] == 3
    assert trace["reranking"]["output_count"] == 2
    assert trace["reranking"]["documents"][0]["rerank_score"] == 0.95


def test_retriever_without_reranker_returns_vector_order() -> None:
    retriever = Retriever(
        embedder=FakeEmbedder(),  # type: ignore[arg-type]
        vector_store=FakeVectorStore(),  # type: ignore[arg-type]
        reranker=None,
        retrieval_k=3,
        top_k=2,
    )
    documents, trace = retriever.retrieve_with_trace("question")
    assert [doc["id"] for doc in documents] == ["gpu", "return"]
    assert trace["reranking"] is None
