import json
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

BENCHMARKS_DIR = Path(
    "data/processed/evaluation/benchmarks"
)

OUTPUT_FILE = (
    BENCHMARKS_DIR
    / "embedding_benchmark.json"
)

NUM_RUNS = 3


def load_questions(
    model_name: str,
) -> list[str]:
    """Load questions from an existing embedding file."""

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
            "Questions list is empty."
        )

    return [
        question["question"]
        for question in questions
    ]


def benchmark_model(
    model_name: str,
) -> dict[str, Any]:
    """Benchmark embedding generation for one model."""

    if model_name not in EMBEDDING_MODELS:
        raise ValueError(
            f"Unknown model: {model_name}"
        )

    ollama_model = EMBEDDING_MODELS[
        model_name
    ]

    questions = load_questions(
        model_name
    )

    strategy = OllamaEmbeddingStrategy(
        model=ollama_model
    )

    # Warm-up.
    strategy.embed(
        [questions[0]]
    )

    times = []

    for _ in range(NUM_RUNS):
        start = time.perf_counter()

        embeddings = strategy.embed(
            questions
        )

        elapsed = (
            time.perf_counter() - start
        )

        if len(embeddings) != len(questions):
            raise ValueError(
                f"Expected {len(questions)} "
                f"embeddings, but received "
                f"{len(embeddings)}."
            )

        times.append(elapsed)

    average_time = mean(times)
    median_time = median(times)

    average_per_question = (
        average_time / len(questions)
    )

    return {
        "model_name": model_name,
        "ollama_model": ollama_model,
        "num_questions": len(questions),
        "num_runs": NUM_RUNS,
        "embedding_dimension": len(
            embeddings[0]
        ),
        "total_times_seconds": times,
        "average_time_seconds": average_time,
        "median_time_seconds": median_time,
        "average_time_ms": (
            average_time * 1000
        ),
        "median_time_ms": (
            median_time * 1000
        ),
        "average_per_question_ms": (
            average_per_question * 1000
        ),
    }


def save_results(
    results: list[dict[str, Any]],
) -> None:
    """Save embedding benchmark results."""

    BENCHMARKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "benchmark": "embedding_generation",
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
    """Print embedding benchmark summary."""

    print("\n" + "=" * 90)
    print("EMBEDDING GENERATION BENCHMARK")
    print("=" * 90)

    print(
        f"{'Model':<15}"
        f"{'Average (ms)':>20}"
        f"{'Median (ms)':>20}"
        f"{'Per Question (ms)':>22}"
    )

    print("-" * 90)

    for result in results:
        print(
            f"{result['model_name']:<15}"
            f"{result['average_time_ms']:>20.2f}"
            f"{result['median_time_ms']:>20.2f}"
            f"{result['average_per_question_ms']:>22.2f}"
        )

    print("=" * 90)


def main() -> None:
    """Benchmark embedding generation for all models."""

    results = []

    print("\n" + "=" * 90)
    print("Starting embedding generation benchmark")
    print("=" * 90)

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
            f"Median: "
            f"{result['median_time_ms']:.2f} ms"
        )

        print(
            f"Per question: "
            f"{result['average_per_question_ms']:.2f} ms"
        )

    save_results(results)

    print_summary(results)

    print(
        f"\nResults saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()