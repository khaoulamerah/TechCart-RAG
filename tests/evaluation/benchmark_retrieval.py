import json
import time
from pathlib import Path
from statistics import mean, median
from typing import Any

from backend.rag.embeddings.models import (
    QDRANT_COLLECTIONS,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


QUESTION_EMBEDDINGS_DIR = Path(
    "data/processed/evaluation/question_embeddings"
)

NUM_RUNS = 3
TOP_K = 5


def load_question_embeddings(
    model_name: str,
) -> list[dict[str, Any]]:
    """Load question embeddings."""

    file_path = (
        QUESTION_EMBEDDINGS_DIR
        / f"question_embeddings_{model_name}.json"
    )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return data["questions"]


def benchmark_model(
    model_name: str,
) -> dict[str, Any]:
    """Benchmark Qdrant retrieval for one model."""

    questions = load_question_embeddings(
        model_name
    )

    collection_name = QDRANT_COLLECTIONS[
        model_name
    ]

    store = QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name=collection_name,
    )

    # Warm-up
    store.search(
        query_vector=questions[0]["embedding"],
        limit=TOP_K,
    )

    times = []

    for _ in range(NUM_RUNS):
        for question in questions:
            start = time.perf_counter()

            store.search(
                query_vector=question["embedding"],
                limit=TOP_K,
            )

            end = time.perf_counter()

            times.append(
                end - start
            )

    average_time = mean(times)
    median_time = median(times)

    return {
        "model_name": model_name,
        "collection_name": collection_name,
        "num_questions": len(questions),
        "num_runs": NUM_RUNS,
        "average_latency_seconds": average_time,
        "median_latency_seconds": median_time,
        "average_latency_ms": (
            average_time * 1000
        ),
        "median_latency_ms": (
            median_time * 1000
        ),
    }


def main() -> None:
    """Benchmark retrieval for all models."""

    results = []

    print("\n" + "=" * 80)
    print("QDRANT RETRIEVAL LATENCY BENCHMARK")
    print("=" * 80)

    for model_name in QDRANT_COLLECTIONS:
        print(
            f"\nBenchmarking: {model_name}"
        )

        result = benchmark_model(
            model_name
        )

        results.append(result)

        print(
            f"Average latency: "
            f"{result['average_latency_ms']:.3f} ms"
        )

        print(
            f"Median latency: "
            f"{result['median_latency_ms']:.3f} ms"
        )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"{'Model':<15}"
        f"{'Average (ms)':>18}"
        f"{'Median (ms)':>18}"
    )

    print("-" * 80)

    for result in results:
        print(
            f"{result['model_name']:<15}"
            f"{result['average_latency_ms']:>18.3f}"
            f"{result['median_latency_ms']:>18.3f}"
        )


if __name__ == "__main__":
    main()