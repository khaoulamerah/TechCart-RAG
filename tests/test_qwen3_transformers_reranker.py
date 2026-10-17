from __future__ import annotations

from typing import Any

import pytest

from backend.rag.reranker.qwen3_transformers import Qwen3TransformersReranker


def make_reranker() -> Qwen3TransformersReranker:
    return Qwen3TransformersReranker(
        model_name="Qwen/Qwen3-Reranker-0.6B",
        device="cpu",
        max_length=2048,
    )


def test_pair_format_has_instruction_query_and_document() -> None:
    reranker = make_reranker()
    pair = reranker._format_pair(
        "What is the return policy?",
        "Eligible items can be returned within 30 days.",
    )

    assert pair.startswith("<Instruct>: Given a web search query")
    assert "<Query>: What is the return policy?" in pair
    assert "<Document>: Eligible items can be returned within 30 days." in pair


def test_rerank_sorts_by_transformers_score(monkeypatch: pytest.MonkeyPatch) -> None:
    reranker = make_reranker()
    score_map = {
        "This document is about graphics cards.": 0.1,
        "Returns are accepted within 30 days.": 0.9,
    }

    monkeypatch.setattr(
        reranker,
        "_score_pair",
        lambda query, document: score_map[document],
    )
    docs: list[dict[str, Any]] = [
        {"id": "gpu", "payload": {"text": "This document is about graphics cards."}},
        {"id": "returns", "payload": {"text": "Returns are accepted within 30 days."}},
    ]

    results = reranker.rerank("What is the return policy?", docs, top_k=2)

    assert [doc["id"] for doc in results] == ["returns", "gpu"]
    assert results[0]["rerank_score"] == pytest.approx(0.9)
    assert results[1]["rerank_score"] == pytest.approx(0.1)


def test_empty_document_gets_zero_score(monkeypatch: pytest.MonkeyPatch) -> None:
    reranker = make_reranker()
    monkeypatch.setattr(
        reranker,
        "_score_pair",
        lambda query, document: 0.5,
    )

    results = reranker.rerank(
        "question",
        [{"id": "empty", "payload": {"text": " "}}],
        top_k=1,
    )

    assert results[0]["rerank_score"] == 0.0


def test_invalid_arguments_are_rejected() -> None:
    reranker = make_reranker()

    with pytest.raises(ValueError, match="Query cannot be empty"):
        reranker.rerank(" ", [], top_k=1)
    with pytest.raises(ValueError, match="top_k must be greater than zero"):
        reranker.rerank("question", [], top_k=0)
