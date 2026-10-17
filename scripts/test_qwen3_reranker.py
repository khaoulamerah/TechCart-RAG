"""Download/load Qwen3-Reranker and run a small local ranking smoke test.

Run inside Docker after rebuilding:
    docker compose exec backend python -m scripts.test_qwen3_reranker
"""

from backend.config.settings import settings
from backend.rag.reranker.qwen3_transformers import Qwen3TransformersReranker


def main() -> None:
    reranker = Qwen3TransformersReranker(
        model_name=settings.RERANKER_MODEL,
        device=settings.RERANKER_DEVICE,
        max_length=settings.RERANKER_MAX_LENGTH,
        instruction=settings.RERANKER_INSTRUCTION,
        max_document_chars=settings.RERANKER_MAX_DOCUMENT_CHARS,
    )

    question = "What is the store return policy?"
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

    reranker.warm_up()
    results = reranker.rerank(question, candidates, top_k=len(candidates))

    print("QWEN3 TRANSFORMERS RERANKER OK")
    print("Model:", settings.RERANKER_MODEL)
    print("Device preference:", settings.RERANKER_DEVICE)
    print("Ranked results:")
    for index, result in enumerate(results, start=1):
        payload = result.get("payload") or {}
        print(
            f"{index}. id={result.get('id')} "
            f"score={result.get('rerank_score', 0.0):.6f} "
            f"text={str(payload.get('text', ''))[:100]!r}"
        )

    if results and results[0].get("id") != "relevant-returns":
        print(
            "WARNING: the relevance example did not rank first. "
            "Inspect model output and prompt before enabling globally."
        )


if __name__ == "__main__":
    main()
