from __future__ import annotations

import math
from typing import Any

import pytest

from backend.rag.reranker.ollama_qwen import OllamaQwenReranker


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeClient:
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.responses = iter(responses)
        self.requests: list[dict[str, Any]] = []

    def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
        self.requests.append({"url": url, "json": json})
        return FakeResponse(next(self.responses))


def make_reranker() -> OllamaQwenReranker:
    return OllamaQwenReranker(
        model_name="dengcao/Qwen3-Reranker-0.6B:Q8_0",
        base_url="http://ollama:11434",
    )


def test_prompt_uses_qwen_reranker_format() -> None:
    reranker = make_reranker()

    prompt = reranker._build_prompt(
        "What is the return policy?",
        "Customers can return eligible products within 30 days.",
    )

    assert "Judge whether the Document" in prompt
    assert "<Instruct>: Given a web search query" in prompt
    assert "<Query>: What is the return policy?" in prompt
    assert "<Document>: Customers can return eligible products" in prompt
    assert prompt.endswith("<|im_start|>assistant\n<think>\n\n</think>\n\n")


def test_score_is_calculated_from_yes_no_logprobs() -> None:
    reranker = make_reranker()
    payload = {
        "response": "yes",
        "logprobs": [
            {
                "token": "yes",
                "logprob": -0.1,
                "top_logprobs": [
                    {"token": "yes", "logprob": -0.1},
                    {"token": "no", "logprob": -2.1},
                ],
            }
        ],
    }

    score = reranker._score_from_response(payload)

    assert score == pytest.approx(1 / (1 + math.exp(-2.0)))


def test_binary_fallback_is_used_when_logprobs_are_missing(caplog: Any) -> None:
    reranker = make_reranker()

    assert reranker._score_from_response({"response": "yes"}) == 1.0
    assert reranker._score_from_response({"response": "no"}) == 0.0
    assert "using binary relevance scores" in caplog.text


def test_rerank_orders_documents_by_score() -> None:
    reranker = make_reranker()
    fake_client = FakeClient(
        [
            {
                "response": "no",
                "logprobs": [
                    {
                        "token": "no",
                        "logprob": -0.1,
                        "top_logprobs": [
                            {"token": "no", "logprob": -0.1},
                            {"token": "yes", "logprob": -2.1},
                        ],
                    }
                ],
            },
            {
                "response": "yes",
                "logprobs": [
                    {
                        "token": "yes",
                        "logprob": -0.1,
                        "top_logprobs": [
                            {"token": "yes", "logprob": -0.1},
                            {"token": "no", "logprob": -2.1},
                        ],
                    }
                ],
            },
        ]
    )
    reranker._client = fake_client  # type: ignore[assignment]
    documents = [
        {"id": "irrelevant", "payload": {"text": "A graphics card warranty."}},
        {"id": "relevant", "payload": {"text": "Our return policy is 30 days."}},
    ]

    results = reranker.rerank("How long do I have to return an item?", documents, 2)

    assert [document["id"] for document in results] == ["relevant", "irrelevant"]
    assert results[0]["rerank_score"] > results[1]["rerank_score"]
    assert fake_client.requests[0]["url"] == "http://ollama:11434/api/generate"
    assert fake_client.requests[0]["json"]["raw"] is True
    assert fake_client.requests[0]["json"]["logprobs"] is True


def test_invalid_arguments_are_rejected() -> None:
    reranker = make_reranker()

    with pytest.raises(ValueError, match="Query cannot be empty"):
        reranker.rerank("   ", [], top_k=1)
    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        reranker.rerank("question", [], top_k=0)
