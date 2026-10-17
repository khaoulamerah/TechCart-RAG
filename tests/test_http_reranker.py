from __future__ import annotations

from typing import Any

import pytest

from backend.rag.reranker.http_client import HttpReranker, RerankerServiceError


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_error: Exception | None = None) -> None:
        self.payload = payload
        self.status_error = status_error

    def raise_for_status(self) -> None:
        if self.status_error:
            raise self.status_error

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeClient:
    def __init__(self) -> None:
        self.get_response = FakeResponse({"status": "ready"})
        self.post_response = FakeResponse({"results": []})
        self.get_calls: list[str] = []
        self.post_calls: list[dict[str, Any]] = []
        self.closed = False

    def get(self, url: str) -> FakeResponse:
        self.get_calls.append(url)
        return self.get_response

    def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
        self.post_calls.append({"url": url, "json": json})
        return self.post_response

    def close(self) -> None:
        self.closed = True


def make_client() -> tuple[HttpReranker, FakeClient]:
    reranker = HttpReranker(
        base_url="http://reranker:8001/",
        model_name="Qwen/Qwen3-Reranker-0.6B",
        timeout_seconds=30,
    )
    fake = FakeClient()
    reranker._client.close()
    reranker._client = fake  # type: ignore[assignment]
    return reranker, fake


def test_warmup_checks_ready_endpoint() -> None:
    reranker, fake = make_client()
    reranker.warm_up()
    assert fake.get_calls == ["http://reranker:8001/health/ready"]


def test_rerank_maps_scores_back_to_original_documents() -> None:
    reranker, fake = make_client()
    fake.post_response = FakeResponse(
        {"results": [{"index": 1, "score": 0.9}, {"index": 0, "score": 0.1}]}
    )
    docs = [
        {"id": "gpu", "score": 0.8, "payload": {"text": "GPU features"}},
        {"id": "returns", "score": 0.6, "payload": {"text": "Return policy"}},
    ]

    results = reranker.rerank("return policy", docs, top_k=2)

    assert [document["id"] for document in results] == ["returns", "gpu"]
    assert results[0]["rerank_score"] == pytest.approx(0.9)
    assert results[0]["payload"] == docs[1]["payload"]
    assert fake.post_calls[0]["url"] == "http://reranker:8001/rerank"
    assert fake.post_calls[0]["json"]["documents"] == [
        {"index": 0, "text": "GPU features"},
        {"index": 1, "text": "Return policy"},
    ]


def test_empty_documents_are_not_sent_to_remote_service() -> None:
    reranker, fake = make_client()
    fake.post_response = FakeResponse({"results": [{"index": 0, "score": 0.7}]})
    docs = [
        {"id": "valid", "payload": {"text": "return policy"}},
        {"id": "empty", "payload": {"text": " "}},
    ]
    results = reranker.rerank("returns", docs, top_k=2)
    assert [item["id"] for item in results] == ["valid", "empty"]
    assert results[1]["rerank_score"] == 0.0
    assert len(fake.post_calls[0]["json"]["documents"]) == 1


def test_invalid_remote_index_is_rejected() -> None:
    reranker, fake = make_client()
    fake.post_response = FakeResponse({"results": [{"index": 99, "score": 0.7}]})
    with pytest.raises(RerankerServiceError, match="invalid or duplicate"):
        reranker.rerank("returns", [{"payload": {"text": "return policy"}}], 1)


def test_empty_query_and_non_positive_top_k_are_rejected() -> None:
    reranker, _ = make_client()
    with pytest.raises(ValueError, match="Query cannot be empty"):
        reranker.rerank(" ", [], 1)
    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        reranker.rerank("query", [], 0)
