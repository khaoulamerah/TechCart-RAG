import json
from pathlib import Path
from typing import Any


EVALUATION_DIR = Path(
    "data/processed/evaluation"
)

BENCHMARKS_DIR = EVALUATION_DIR / "benchmarks"

METRICS_FILE = EVALUATION_DIR / "metrics.json"

EMBEDDING_BENCHMARK_FILE = (
    BENCHMARKS_DIR / "embedding_benchmark.json"
)

RETRIEVAL_BENCHMARK_FILE = (
    BENCHMARKS_DIR / "retrieval_benchmark.json"
)



def load_json(file_path: Path) -> dict[str, Any]:

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected a JSON object in {file_path}"
        )

    return data



def validate_models_list(
    data: dict[str, Any],
    file_path: Path,
) -> list[dict[str, Any]]:

    if "models" not in data:
        raise ValueError(
            f"'models' field not found in {file_path}"
        )

    models = data["models"]

    if not isinstance(models, list):
        raise ValueError(
            f"'models' must be a list in {file_path}"
        )

    if not models:
        raise ValueError(
            f"'models' list is empty in {file_path}"
        )

    return models


# Load evaluation results

def load_metrics() -> list[dict[str, Any]]:

    data = load_json(METRICS_FILE)

    return validate_models_list(
        data,
        METRICS_FILE,
    )


def load_embedding_benchmark() -> list[dict[str, Any]]:

    data = load_json(
        EMBEDDING_BENCHMARK_FILE
    )

    return validate_models_list(
        data,
        EMBEDDING_BENCHMARK_FILE,
    )


def load_retrieval_benchmark() -> list[dict[str, Any]]:

    data = load_json(
        RETRIEVAL_BENCHMARK_FILE
    )

    return validate_models_list(
        data,
        RETRIEVAL_BENCHMARK_FILE,
    )


def index_by_model(
    results: list[dict[str, Any]],
    source_name: str,
) -> dict[str, dict[str, Any]]:

    indexed: dict[str, dict[str, Any]] = {}

    for result in results:
        if "model_name" not in result:
            raise ValueError(
                f"'model_name' missing in {source_name}"
            )

        model_name = result["model_name"]

        if model_name in indexed:
            raise ValueError(
                f"Duplicate model '{model_name}' "
                f"found in {source_name}"
            )

        indexed[model_name] = result

    return indexed


# Merge results

def merge_results(
    metrics: list[dict[str, Any]],
    embedding_benchmark: list[dict[str, Any]],
    retrieval_benchmark: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    metrics_by_model = index_by_model(
        metrics,
        "metrics.json",
    )

    embedding_by_model = index_by_model(
        embedding_benchmark,
        "embedding_benchmark.json",
    )

    retrieval_by_model = index_by_model(
        retrieval_benchmark,
        "retrieval_benchmark.json",
    )

    model_names = set(metrics_by_model)

    embedding_names = set(
        embedding_by_model
    )

    retrieval_names = set(
        retrieval_by_model
    )

    if model_names != embedding_names:
        raise ValueError(
            "Model mismatch between metrics.json "
            "and embedding_benchmark.json.\n"
            f"Metrics: {sorted(model_names)}\n"
            f"Embedding benchmark: "
            f"{sorted(embedding_names)}"
        )

    if model_names != retrieval_names:
        raise ValueError(
            "Model mismatch between metrics.json "
            "and retrieval_benchmark.json.\n"
            f"Metrics: {sorted(model_names)}\n"
            f"Retrieval benchmark: "
            f"{sorted(retrieval_names)}"
        )

    merged_results = []

    for model_name in metrics_by_model:
        quality = metrics_by_model[
            model_name
        ]

        embedding = embedding_by_model[
            model_name
        ]

        retrieval = retrieval_by_model[
            model_name
        ]

        result = {
            "model_name": model_name,
            "ollama_model": quality.get(
                "ollama_model",
                embedding.get(
                    "ollama_model",
                    "unknown",
                ),
            ),
            "embedding_dimension": embedding.get(
                "embedding_dimension"
            ),
            "num_questions": quality.get(
                "num_questions"
            ),
            "recall_at_1": quality.get(
                "recall_at_1"
            ),
            "recall_at_5": quality.get(
                "recall_at_5"
            ),
            "mrr_at_5": quality.get(
                "mrr_at_5"
            ),
            "embedding_average_ms": embedding.get(
                "average_time_ms"
            ),
            "embedding_median_ms": embedding.get(
                "median_time_ms"
            ),
            "embedding_per_question_ms": embedding.get(
                "average_per_question_ms"
            ),
            "retrieval_average_ms": retrieval.get(
                "average_latency_ms"
            ),
            "retrieval_median_ms": retrieval.get(
                "median_latency_ms"
            ),
        }

        merged_results.append(result)

    return merged_results


# Formatting helpers
def format_percentage(
    value: float | None,
) -> str:
    if value is None:
        return "N/A"

    return f"{value * 100:.1f}%"


def format_ms(
    value: float | None,
) -> str:

    if value is None:
        return "N/A"

    return f"{value:.2f}"


# Print comparison table

def print_comparison_table(
    results: list[dict[str, Any]],
) -> None:
    """
    Print the final model comparison table.
    """

    print()
    print("=" * 125)
    print("EMBEDDING MODEL COMPARISON")
    print("=" * 125)

    header = (
        f"{'Model':<12}"
        f"{'Dim':>7}"
        f"{'R@1':>10}"
        f"{'R@5':>10}"
        f"{'MRR@5':>10}"
        f"{'Embed ms':>13}"
        f"{'Search ms':>13}"
    )

    print(header)
    print("-" * 125)

    for result in results:
        print(
            f"{result['model_name']:<12}"
            f"{str(result['embedding_dimension']):>7}"
            f"{format_percentage(result['recall_at_1']):>10}"
            f"{format_percentage(result['recall_at_5']):>10}"
            f"{format_percentage(result['mrr_at_5']):>10}"
            f"{format_ms(result['embedding_per_question_ms']):>13}"
            f"{format_ms(result['retrieval_average_ms']):>13}"
        )

    print("=" * 125)

    print()
    print("Legend:")
    print("  R@1       = Recall@1")
    print("  R@5       = Recall@5")
    print("  MRR@5     = Mean Reciprocal Rank@5")
    print("  Embed ms  = average embedding time per question")
    print("  Search ms = average Qdrant retrieval latency")
    print()


# ============================================================
# Print detailed comparison
# ============================================================


def print_detailed_results(
    results: list[dict[str, Any]],
) -> None:
    """
    Print additional details for each model.
    """

    print()
    print("=" * 100)
    print("DETAILED RESULTS")
    print("=" * 100)

    for result in results:
        print()
        print(f"Model: {result['model_name']}")
        print(
            f"Ollama model: "
            f"{result['ollama_model']}"
        )
        print(
            f"Embedding dimension: "
            f"{result['embedding_dimension']}"
        )
        print(
            f"Questions: "
            f"{result['num_questions']}"
        )

        print()
        print("Retrieval quality:")
        print(
            f"  Recall@1 : "
            f"{format_percentage(result['recall_at_1'])}"
        )
        print(
            f"  Recall@5 : "
            f"{format_percentage(result['recall_at_5'])}"
        )
        print(
            f"  MRR@5    : "
            f"{format_percentage(result['mrr_at_5'])}"
        )

        print()
        print("Embedding speed:")
        print(
            f"  Average : "
            f"{format_ms(result['embedding_average_ms'])} ms"
        )
        print(
            f"  Median  : "
            f"{format_ms(result['embedding_median_ms'])} ms"
        )
        print(
            f"  Per question : "
            f"{format_ms(result['embedding_per_question_ms'])} ms"
        )

        print()
        print("Retrieval speed:")
        print(
            f"  Average : "
            f"{format_ms(result['retrieval_average_ms'])} ms"
        )
        print(
            f"  Median  : "
            f"{format_ms(result['retrieval_median_ms'])} ms"
        )

        print("-" * 100)



def save_comparison(
    results: list[dict[str, Any]],
) -> Path:

    output_file = (
        BENCHMARKS_DIR
        / "model_comparison.json"
    )

    output = {
        "comparison": "embedding_models",
        "num_models": len(results),
        "models": results,
    }

    BENCHMARKS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    return output_file


def main() -> None:

    print()
    print("=" * 100)
    print("Starting embedding model comparison")
    print("=" * 100)

    print()
    print("Loading retrieval quality metrics...")
    metrics = load_metrics()

    print(
        f"Loaded {len(metrics)} models."
    )

    print()
    print("Loading embedding benchmark...")
    embedding_benchmark = (
        load_embedding_benchmark()
    )

    print(
        f"Loaded "
        f"{len(embedding_benchmark)} models."
    )

    print()
    print("Loading retrieval benchmark...")
    retrieval_benchmark = (
        load_retrieval_benchmark()
    )

    print(
        f"Loaded "
        f"{len(retrieval_benchmark)} models."
    )

    print()
    print("Merging results...")

    results = merge_results(
        metrics=metrics,
        embedding_benchmark=embedding_benchmark,
        retrieval_benchmark=retrieval_benchmark,
    )

    print_comparison_table(results)

    print_detailed_results(results)

    output_file = save_comparison(results)

    print()
    print("=" * 100)
    print("Comparison completed successfully.")
    print("=" * 100)
    print()
    print(
        f"Combined results saved to:\n"
        f"{output_file}"
    )
    print()


if __name__ == "__main__":
    main()