import json
from pathlib import Path
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


def load_question_embeddings(
    file_path: Path,
) -> dict[str, Any]:
    """Load question embeddings from JSON."""

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

    if not isinstance(
        data["questions"],
        list,
    ):
        raise ValueError(
            "'questions' must contain a list."
        )

    return data


def retrieve_questions(
    model_name: str,
) -> list[dict[str, Any]]:
    """Retrieve top-k chunks for all questions."""

    if model_name not in QDRANT_COLLECTIONS:
        raise ValueError(
            f"Unknown model: {model_name}"
        )

    embeddings_file = (
        QUESTION_EMBEDDINGS_DIR
        / f"question_embeddings_{model_name}.json"
    )

    data = load_question_embeddings(
        embeddings_file
    )

    questions = data["questions"]

    collection_name = QDRANT_COLLECTIONS[
        model_name
    ]

    print("\n" + "=" * 70)
    print(f"MODEL: {model_name}")
    print(f"COLLECTION: {collection_name}")
    print("=" * 70)

    store = QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name=collection_name,
    )

    results = []

    for question in questions:
        question_id = question["id"]
        question_text = question["question"]
        query_vector = question["embedding"]

        retrieved = store.search(
            query_vector=query_vector,
            limit=5,
        )

        retrieved_documents = [
            result["payload"]["document_id"]
            for result in retrieved
        ]

        retrieved_chunks = [
            result["payload"]["chunk_id"]
            for result in retrieved
        ]

        result = {
            "id": question_id,
            "question": question_text,
            "relevant_documents": (
                question["relevant_documents"]
            ),
            "retrieved_documents": (
                retrieved_documents
            ),
            "retrieved_chunks": (
                retrieved_chunks
            ),
            "scores": [
                result["score"]
                for result in retrieved
            ],
        }

        results.append(result)

    return results


def save_results(
    file_path: Path,
    model_name: str,
    results: list[dict[str, Any]],
) -> None:
    """Save retrieval results."""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "model_name": model_name,
        "top_k": 5,
        "num_questions": len(results),
        "results": results,
    }

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_results(
    results: list[dict[str, Any]],
) -> None:
    """Print retrieval results."""

    for result in results:
        print("\n" + "-" * 70)

        print(
            f"Question ID: "
            f"{result['id']}"
        )

        print(
            f"Question: "
            f"{result['question']}"
        )

        print(
            f"Expected: "
            f"{result['relevant_documents']}"
        )

        print("Retrieved:")

        for rank, (
            document,
            chunk,
            score,
        ) in enumerate(
            zip(
                result["retrieved_documents"],
                result["retrieved_chunks"],
                result["scores"],
            ),
            start=1,
        ):
            print(
                f"  {rank}. "
                f"{document} "
                f"({chunk}) "
                f"score={score:.4f}"
            )


def main() -> None:
    """Run retrieval for all models."""

    output_dir = Path(
        "data/processed/evaluation/retrieval_results"
    )

    for model_name in QDRANT_COLLECTIONS:
        results = retrieve_questions(
            model_name
        )

        output_file = (
            output_dir
            / f"retrieval_{model_name}.json"
        )

        save_results(
            file_path=output_file,
            model_name=model_name,
            results=results,
        )

        print_results(results)

        print(
            f"\nSaved results to: "
            f"{output_file}"
        )

    print("\n" + "=" * 70)
    print("RETRIEVAL COMPLETED FOR ALL MODELS")
    print("=" * 70)


if __name__ == "__main__":
    main()