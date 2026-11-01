from unittest.mock import Mock, patch

import httpx
import pytest

from backend.rag.reranker.http_client import HttpReranker


def _documents():
    return [
        {"id": "low", "score": 0.2, "payload": {"text": "low score"}},
        {"id": "high", "score": 0.9, "payload": {"text": "high score"}},
    ]


def test_http_reranker_returns_service_ranking():
    documents = _documents()
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "documents": [documents[1], documents[0]],
        "model": "test",
    }

    with patch("backend.rag.reranker.http_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = response
        result = HttpReranker(timeout_seconds=1).rerank("question", documents, 1)

    assert [item["id"] for item in result] == ["high"]
    client.post.assert_called_once()


def test_http_reranker_falls_back_to_vector_scores_on_service_error():
    documents = _documents()

    with patch("backend.rag.reranker.http_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.side_effect = httpx.ConnectError("service unavailable")
        result = HttpReranker(timeout_seconds=1).rerank("question", documents, 1)

    assert [item["id"] for item in result] == ["high"]


def test_http_reranker_validates_empty_query():
    with pytest.raises(ValueError, match="Query cannot be empty"):
        HttpReranker().rerank("  ", _documents(), 1)
