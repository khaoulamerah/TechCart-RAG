import time
from pathlib import Path
from statistics import mean, median
from typing import Any

from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.embeddings.models import (
    EMBEDDING_MODELS,
)


QUESTION_EMBEDDINGS_DIR = Path(
    "data/processed/evaluation/question_embeddings"
)

NUM_RUNS = 3


def load_questions(
    model_name: str,
) -> list[str]:
    """Load questions from the existing embedding file."""

    import json

    file_path = (
        QUESTION_EMBEDDINGS_DIR
        / f"question_embeddings_{model_name}.json"
    )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return [
        question["question"]
        for question in data["questions"]
    ]


def benchmark_model(
    model_name: str,
) -> dict[str, Any]:
    """Benchmark embedding generation for one model."""

    ollama_model = EMBEDDING_MODELS[
        model_name
    ]

    questions = load_questions(
        model_name
    )

    strategy = OllamaEmbeddingStrategy(
        model=ollama_model
    )

    # Warm-up
    strategy.embed(
        [questions[0]]
    )

    times = []

    for _ in range(NUM_RUNS):
        start = time.perf_counter()

        strategy.embed(
            questions
        )

        end = time.perf_counter()

        elapsed = end - start
        times.append(elapsed)

    average_time = mean(times)
    median_time = median(times)

    return {
        "model_name": model_name,
        "ollama_model": ollama_model,
        "num_questions": len(questions),
        "num_runs": NUM_RUNS,
        "total_times_seconds": times,
        "average_time_seconds": average_time,
        "median_time_seconds": median_time,
        "average_time_ms": average_time * 1000,
        "median_time_ms": median_time * 1000,
        "average_per_question_ms": (
            average_time
            / len(questions)
            * 1000
        ),
    }


def main() -> None:
    """Benchmark all embedding models."""

    results = []

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATION BENCHMARK")
    print("=" * 80)

    for model_name in EMBEDDING_MODELS:
        print(
            f"\nBenchmarking: {model_name}"
        )

        result = benchmark_model(
            model_name
        )

        results.append(result)

        print(
            f"Average: "
            f"{result['average_time_ms']:.2f} ms"
        )

        print(
            f"Per question: "
            f"{result['average_per_question_ms']:.2f} ms"
        )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"{'Model':<15}"
        f"{'Total (ms)':>15}"
        f"{'Per Question':>18}"
    )

    print("-" * 80)

    for result in results:
        print(
            f"{result['model_name']:<15}"
            f"{result['average_time_ms']:>15.2f}"
            f"{result['average_per_question_ms']:>18.2f}"
        )


if __name__ == "__main__":
    main()