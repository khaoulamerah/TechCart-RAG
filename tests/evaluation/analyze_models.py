import json
from pathlib import Path
from typing import Any


EVALUATION_DIR = Path(
    "data/processed/evaluation"
)

COMPARISON_FILE = (
    EVALUATION_DIR
    / "benchmarks"
    / "model_comparison.json"
)

OUTPUT_FILE = (
    EVALUATION_DIR
    / "benchmarks"
    / "model_analysis.json"
)


def load_comparison() -> list[dict[str, Any]]:
    """Load the combined model comparison."""

    if not COMPARISON_FILE.exists():
        raise FileNotFoundError(
            f"Comparison file not found: "
            f"{COMPARISON_FILE}"
        )

    with COMPARISON_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "model_comparison.json must contain "
            "a JSON object."
        )

    if "models" not in data:
        raise ValueError(
            "'models' field not found."
        )

    models = data["models"]

    if not isinstance(models, list):
        raise ValueError(
            "'models' must be a list."
        )

    if not models:
        raise ValueError(
            "'models' list is empty."
        )

    return models


def dominates(
    model_a: dict[str, Any],
    model_b: dict[str, Any],
) -> bool:

    quality_a = [
        model_a["recall_at_1"],
        model_a["recall_at_5"],
        model_a["mrr_at_5"],
    ]

    quality_b = [
        model_b["recall_at_1"],
        model_b["recall_at_5"],
        model_b["mrr_at_5"],
    ]

    speed_a = [
        model_a["embedding_per_question_ms"],
        model_a["retrieval_average_ms"],
    ]

    speed_b = [
        model_b["embedding_per_question_ms"],
        model_b["retrieval_average_ms"],
    ]

    # A must be at least as good as B
    # on every dimension.

    quality_not_worse = all(
        a >= b
        for a, b in zip(
            quality_a,
            quality_b,
        )
    )

    speed_not_worse = all(
        a <= b
        for a, b in zip(
            speed_a,
            speed_b,
        )
    )

    if not quality_not_worse:
        return False

    if not speed_not_worse:
        return False


    quality_better = any(
        a > b
        for a, b in zip(
            quality_a,
            quality_b,
        )
    )

    speed_better = any(
        a < b
        for a, b in zip(
            speed_a,
            speed_b,
        )
    )

    return quality_better or speed_better


def find_pareto_efficient_models(
    models: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    efficient_models = []

    for candidate in models:
        dominated = False

        for other in models:
            if candidate is other:
                continue

            if dominates(
                other,
                candidate,
            ):
                dominated = True
                break

        if not dominated:
            efficient_models.append(candidate)

    return efficient_models


def find_best_quality_model(
    models: list[dict[str, Any]],
) -> dict[str, Any]:

    return max(
        models,
        key=lambda model: (
            model["mrr_at_5"],
            model["recall_at_1"],
            model["recall_at_5"],
        ),
    )



# Speed comparison
def find_fastest_embedding_model(
    models: list[dict[str, Any]],
) -> dict[str, Any]:

    return min(
        models,
        key=lambda model: (
            model["embedding_per_question_ms"]
        ),
    )


def find_fastest_retrieval_model(
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    """Find the model with the lowest Qdrant latency."""

    return min(
        models,
        key=lambda model: (
            model["retrieval_average_ms"]
        ),
    )


def print_pareto_analysis(
    pareto_models: list[dict[str, Any]],
) -> None:
    """Print Pareto-efficient models."""

    print()
    print("=" * 100)
    print("PARETO-EFFICIENT MODELS")
    print("=" * 100)

    print(
        "These models are not simultaneously worse in "
        "both quality and speed."
    )

    print()

    for model in pareto_models:
        print(
            f"- {model['model_name']}"
        )

    print("=" * 100)


def print_quality_analysis(
    models: list[dict[str, Any]],
) -> dict[str, Any]:

    best_quality = find_best_quality_model(
        models
    )

    print()
    print("=" * 100)
    print("RETRIEVAL QUALITY")
    print("=" * 100)

    print(
        f"Best measured quality: "
        f"{best_quality['model_name']}"
    )

    print(
        f"Recall@1 : "
        f"{best_quality['recall_at_1'] * 100:.1f}%"
    )

    print(
        f"Recall@5 : "
        f"{best_quality['recall_at_5'] * 100:.1f}%"
    )

    print(
        f"MRR@5    : "
        f"{best_quality['mrr_at_5'] * 100:.1f}%"
    )

    print("=" * 100)

    return best_quality


def print_speed_analysis(
    models: list[dict[str, Any]],
) -> None:
    """Print fastest models."""

    fastest_embedding = (
        find_fastest_embedding_model(models)
    )

    fastest_retrieval = (
        find_fastest_retrieval_model(models)
    )

    print()
    print("=" * 100)
    print("SPEED")
    print("=" * 100)

    print(
        f"Fastest embedding: "
        f"{fastest_embedding['model_name']} "
        f"("
        f"{fastest_embedding['embedding_per_question_ms']:.2f}"
        f" ms/question)"
    )

    print(
        f"Fastest retrieval: "
        f"{fastest_retrieval['model_name']} "
        f"("
        f"{fastest_retrieval['retrieval_average_ms']:.2f}"
        f" ms)"
    )

    print("=" * 100)


def save_analysis(
    models: list[dict[str, Any]],
    pareto_models: list[dict[str, Any]],
    best_quality: dict[str, Any],
) -> None:
    """Save analysis results."""

    fastest_embedding = (
        find_fastest_embedding_model(models)
    )

    fastest_retrieval = (
        find_fastest_retrieval_model(models)
    )

    output = {
        "analysis": "embedding_model_analysis",
        "num_models": len(models),
        "pareto_efficient_models": [
            model["model_name"]
            for model in pareto_models
        ],
        "best_retrieval_quality": (
            best_quality["model_name"]
        ),
        "fastest_embedding": (
            fastest_embedding["model_name"]
        ),
        "fastest_retrieval": (
            fastest_retrieval["model_name"]
        ),
        "models": models,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def main() -> None:

    print()
    print("=" * 100)
    print("EMBEDDING MODEL ANALYSIS")
    print("=" * 100)

    models = load_comparison()

    print(
        f"\nLoaded {len(models)} models."
    )

    pareto_models = (
        find_pareto_efficient_models(
            models
        )
    )

    print_pareto_analysis(
        pareto_models
    )

    best_quality = print_quality_analysis(
        models
    )

    print_speed_analysis(models)

    save_analysis(
        models=models,
        pareto_models=pareto_models,
        best_quality=best_quality,
    )

    print()
    print("=" * 100)
    print("ANALYSIS COMPLETED")
    print("=" * 100)

    print()
    print(
        f"Analysis saved to:\n"
        f"{OUTPUT_FILE}"
    )

    print()


if __name__ == "__main__":
    main()