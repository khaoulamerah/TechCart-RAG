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

BENCHMARKS_DIR = Path(
    "data/processed/evaluation/benchmarks"
)

OUTPUT_FILE = (
    BENCHMARKS_DIR
    / "retrieval_benchmark.json"
)

NUM_RUNS = 3
TOP_K = 5


def load_question_embeddings(
    model_name: str,
) -> list[dict[str, Any]]:
    """Load question embeddings for one model."""

    file_path = (
        QUESTION_EMBEDDINGS_DIR
        / f"question_embeddings_{model_name}.json"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Question embeddings file not found: "
            f"{file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Question embeddings JSON must contain "
            "an object."
        )

    if "questions" not in data:
        raise ValueError(
            "Question embeddings JSON must contain "
            "'questions'."
        )

    questions = data["questions"]

    if not isinstance(questions, list):
        raise ValueError(
            "'questions' must contain a list."
        )

    if not questions:
        raise ValueError(
            "Question embeddings list is empty."
        )

    return questions


def benchmark_model(
    model_name: str,
) -> dict[str, Any]:
    """Benchmark Qdrant retrieval for one model."""

    if model_name not in QDRANT_COLLECTIONS:
        raise ValueError(
            f"Unknown model: {model_name}"
        )

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

    # Warm-up.
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

            elapsed = (
                time.perf_counter() - start
            )

            times.append(elapsed)

    average_time = mean(times)
    median_time = median(times)

    return {
        "model_name": model_name,
        "collection_name": collection_name,
        "num_questions": len(questions),
        "num_runs": NUM_RUNS,
        "top_k": TOP_K,
        "num_measurements": len(times),
        "average_latency_seconds": average_time,
        "median_latency_seconds": median_time,
        "average_latency_ms": (
            average_time * 1000
        ),
        "median_latency_ms": (
            median_time * 1000
        ),
    }


def save_results(
    results: list[dict[str, Any]],
) -> None:
    """Save retrieval benchmark results."""

    BENCHMARKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "benchmark": "qdrant_retrieval_latency",
        "num_models": len(results),
        "models": results,
    }

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_summary(
    results: list[dict[str, Any]],
) -> None:
    """Print retrieval benchmark summary."""

    print("\n" + "=" * 90)
    print("QDRANT RETRIEVAL LATENCY BENCHMARK")
    print("=" * 90)

    print(
        f"{'Model':<15}"
        f"{'Average (ms)':>20}"
        f"{'Median (ms)':>20}"
    )

    print("-" * 90)

    for result in results:
        print(
            f"{result['model_name']:<15}"
            f"{result['average_latency_ms']:>20.3f}"
            f"{result['median_latency_ms']:>20.3f}"
        )

    print("=" * 90)


def main() -> None:
    """Benchmark retrieval for all models."""

    results = []

    print("\n" + "=" * 90)
    print("Starting Qdrant retrieval benchmark")
    print("=" * 90)

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

    save_results(results)

    print_summary(results)

    print(
        f"\nResults saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()