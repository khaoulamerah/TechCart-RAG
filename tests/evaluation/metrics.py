import json
from pathlib import Path
from typing import Any

from backend.rag.embeddings.models import EMBEDDING_MODELS


RETRIEVAL_RESULTS_DIR = Path(
    "data/processed/evaluation/retrieval_results"
)


def load_retrieval_results(
    file_path: Path,
) -> dict[str, Any]:
    """Load retrieval results from a JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Retrieval results file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Retrieval results JSON must contain an object."
        )

    if "results" not in data:
        raise ValueError(
            "Retrieval results JSON must contain 'results'."
        )

    if not isinstance(data["results"], list):
        raise ValueError(
            "'results' must contain a list."
        )

    return data


def is_relevant(
    retrieved_document: str,
    relevant_documents: list[str],
) -> bool:

    return retrieved_document in relevant_documents


def calculate_recall_at_k(
    results: list[dict[str, Any]],
    k: int,
) -> float:

    if not results:
        return 0.0

    successful_queries = 0

    for result in results:
        relevant_documents = result[
            "relevant_documents"
        ]

        retrieved_documents = result[
            "retrieved_documents"
        ]

        top_k = retrieved_documents[:k]

        found = any(
            is_relevant(
                document,
                relevant_documents,
            )
            for document in top_k
        )

        if found:
            successful_queries += 1

    return successful_queries / len(results)


def calculate_mrr(
    results: list[dict[str, Any]],
    k: int,
) -> float:

    if not results:
        return 0.0

    reciprocal_ranks = []

    for result in results:
        relevant_documents = result[
            "relevant_documents"
        ]

        retrieved_documents = result[
            "retrieved_documents"
        ]

        top_k = retrieved_documents[:k]

        reciprocal_rank = 0.0

        for rank, document in enumerate(
            top_k,
            start=1,
        ):
            if is_relevant(
                document,
                relevant_documents,
            ):
                reciprocal_rank = 1.0 / rank
                break

        reciprocal_ranks.append(
            reciprocal_rank
        )

    return sum(reciprocal_ranks) / len(
        reciprocal_ranks
    )


def calculate_metrics(
    results: list[dict[str, Any]],
) -> dict[str, float]:

    return {
        "recall_at_1": calculate_recall_at_k(
            results,
            k=1,
        ),
        "recall_at_5": calculate_recall_at_k(
            results,
            k=5,
        ),
        "mrr_at_5": calculate_mrr(
            results,
            k=5,
        ),
    }


def evaluate_model(
    model_name: str,
) -> dict[str, Any]:

    file_path = (
        RETRIEVAL_RESULTS_DIR
        / f"retrieval_{model_name}.json"
    )

    data = load_retrieval_results(
        file_path
    )

    results = data["results"]

    metrics = calculate_metrics(
        results
    )

    return {
        "model_name": model_name,
        "ollama_model": EMBEDDING_MODELS[
            model_name
        ],
        "num_questions": len(results),
        **metrics,
    }


def evaluate_all_models() -> list[dict[str, Any]]:
    """Evaluate all embedding models."""

    evaluation_results = []

    for model_name in EMBEDDING_MODELS:
        print(
            f"Evaluating model: {model_name}"
        )

        result = evaluate_model(
            model_name
        )

        evaluation_results.append(
            result
        )

    return evaluation_results


def save_metrics(
    results: list[dict[str, Any]],
    output_file: Path,
) -> None:

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "num_models": len(results),
        "models": results,
    }

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_comparison(
    results: list[dict[str, Any]],
) -> None:

    print("\n")
    print("=" * 90)
    print("EMBEDDING MODEL COMPARISON")
    print("=" * 90)

    header = (
        f"{'Model':<15}"
        f"{'Recall@1':>12}"
        f"{'Recall@5':>12}"
        f"{'MRR@5':>12}"
    )

    print(header)
    print("-" * 90)

    for result in results:
        print(
            f"{result['model_name']:<15}"
            f"{result['recall_at_1']:>12.4f}"
            f"{result['recall_at_5']:>12.4f}"
            f"{result['mrr_at_5']:>12.4f}"
        )

    print("=" * 90)


def main() -> None:
    """Run the complete retrieval evaluation."""

    results = evaluate_all_models()

    output_file = (
        Path(
            "data/processed/evaluation"
        )
        / "metrics.json"
    )

    save_metrics(
        results,
        output_file,
    )

    print_comparison(
        results
    )

    print(
        f"\nMetrics saved to: {output_file}"
    )


if __name__ == "__main__":
    main()