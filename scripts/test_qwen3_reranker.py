"""Smoke-test the dedicated HTTP reranker from inside the backend container.

Run with:
    docker compose exec backend python -m scripts.test_qwen3_reranker
"""

from backend.config.settings import settings
from backend.rag.reranker.http_client import HttpReranker


def main() -> None:
    if not settings.RERANKER_ENABLED:
        raise SystemExit("Set RERANKER_ENABLED=true in .env before this test.")

    reranker = HttpReranker(
        base_url=settings.RERANKER_BASE_URL,
        model_name=settings.RERANKER_MODEL,
        timeout_seconds=settings.RERANKER_TIMEOUT_SECONDS,
        max_document_chars=settings.RERANKER_MAX_DOCUMENT_CHARS,
    )
    try:
        reranker.warm_up()
        query = "What is the store return policy?"
        candidates = [
            {
                "id": "irrelevant-gpu",
                "payload": {
                    "text": "This document describes graphics card specifications and GPU memory."
                },
            },
            {
                "id": "relevant-returns",
                "payload": {
                    "text": "Customers can return eligible products according to the store's return policy."
                },
            },
        ]
        results = reranker.rerank(query, candidates, top_k=2)
        print("RERANKER HTTP SMOKE TEST PASSED")
        print("Endpoint:", settings.RERANKER_BASE_URL)
        print("Model:", settings.RERANKER_MODEL)
        for rank, result in enumerate(results, start=1):
            text = (result.get("payload") or {}).get("text", "")
            print(
                f"{rank}. id={result.get('id')} "
                f"score={result.get('rerank_score', 0.0):.6f} "
                f"text={text[:100]!r}"
            )
        if results and results[0].get("id") != "relevant-returns":
            print(
                "WARNING: the expected document did not rank first. "
                "Inspect model prompt and quality before relying on this example."
            )
    finally:
        reranker.close()


if __name__ == "__main__":
    main()
