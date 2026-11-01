"""Smoke-test the dedicated Qwen3 reranker HTTP service.

Run after starting the Compose stack:
    docker compose exec backend python -m scripts.test_qwen3_reranker
"""

import sys

import httpx

from backend.config.settings import settings
from backend.rag.reranker.http_client import HttpReranker


def main() -> None:
    base_url = settings.RERANKER_BASE_URL.rstrip("/")
    try:
        response = httpx.get(f"{base_url}/health/ready", timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        print(
            "RERANKER NOT READY: the service or model is not ready yet. "
            "Chat will continue with vector ranking while it retries."
        )
        print(f"Details: {exc}")
        sys.exit(1)

    candidates = [
        {
            "id": "gpu-guide",
            "score": 0.91,
            "payload": {
                "text": "This document describes graphics card specifications and GPU memory."
            },
        },
        {
            "id": "return-policy",
            "score": 0.72,
            "payload": {
                "text": "Customers can return eligible products according to the store's return policy."
            },
        },
    ]

    reranker = HttpReranker(
        base_url=base_url,
        model_name=settings.RERANKER_MODEL,
        timeout_seconds=settings.RERANKER_TIMEOUT_SECONDS,
    )
    results = reranker.rerank(
        "What is the store return policy?",
        candidates,
        top_k=len(candidates),
    )

    print("QWEN3 HTTP RERANKER SERVICE OK")
    print("Model:", settings.RERANKER_MODEL)
    for index, result in enumerate(results, start=1):
        payload = result.get("payload") or {}
        print(
            f"{index}. id={result.get('id')} "
            f"rerank_score={result.get('rerank_score')} "
            f"text={str(payload.get('text', ''))[:100]!r}"
        )

    if results and results[0].get("id") != "return-policy":
        print(
            "WARNING: the expected return-policy passage was not ranked first. "
            "Check model configuration and the service logs."
        )


if __name__ == "__main__":
    main()
