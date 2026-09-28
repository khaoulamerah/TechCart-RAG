import json
from pathlib import Path
from typing import Any

from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.embeddings.models import (
    EMBEDDING_MODELS,
)

from tests.evaluation.loader import (
    QUESTIONS_FILE,
    load_questions,
)


OUTPUT_DIR = Path(
    "data/processed/evaluation/question_embeddings"
)


def save_question_embeddings(
    file_path: Path,
    model_name: str,
    ollama_model: str,
    questions: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    """Save question embeddings."""

    if len(questions) != len(embeddings):
        raise ValueError(
            "Number of questions does not match "
            "number of embeddings."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = []

    for question, embedding in zip(
        questions,
        embeddings,
    ):
        data.append(
            {
                "id": question["id"],
                "question": question["question"],
                "relevant_documents": (
                    question["relevant_documents"]
                ),
                "embedding": embedding,
            }
        )

    output = {
        "model_name": model_name,
        "ollama_model": ollama_model,
        "vector_dimension": len(
            embeddings[0]
        ),
        "num_questions": len(questions),
        "questions": data,
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


def generate_question_embeddings(
    model_name: str,
    ollama_model: str,
    questions: list[dict[str, Any]],
) -> list[list[float]]:
    """Generate embeddings for evaluation questions."""

    print("\n" + "=" * 60)
    print(f"Model: {model_name}")
    print(f"Ollama model: {ollama_model}")
    print("=" * 60)

    texts = [
        question["question"]
        for question in questions
    ]

    embedder = OllamaEmbeddingStrategy(
        model=ollama_model,
    )

    print(
        f"Generating embeddings for "
        f"{len(texts)} questions..."
    )

    embeddings = embedder.embed(texts)

    if len(embeddings) != len(texts):
        raise ValueError(
            f"Expected {len(texts)} embeddings, "
            f"but received {len(embeddings)}."
        )

    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Vector dimension: "
        f"{len(embeddings[0])}"
    )

    print("\nFirst question:")

    print(
        f"ID: {questions[0]['id']}"
    )

    print(
        f"Question: "
        f"{questions[0]['question']}"
    )

    print(
        f"First 5 values: "
        f"{embeddings[0][:5]}"
    )

    return embeddings


def main() -> None:
    """Generate embeddings for all evaluation questions."""

    print(
        f"Loading questions from: "
        f"{QUESTIONS_FILE}"
    )

    questions = load_questions()

    print(
        f"Number of questions: "
        f"{len(questions)}"
    )

    for model_name, ollama_model in (
        EMBEDDING_MODELS.items()
    ):
        embeddings = generate_question_embeddings(
            model_name=model_name,
            ollama_model=ollama_model,
            questions=questions,
        )

        output_file = (
            OUTPUT_DIR
            / f"question_embeddings_{model_name}.json"
        )

        save_question_embeddings(
            file_path=output_file,
            model_name=model_name,
            ollama_model=ollama_model,
            questions=questions,
            embeddings=embeddings,
        )

        print(
            f"\nSaved to: {output_file}"
        )

    print("\n" + "=" * 60)
    print(
        "ALL QUESTION EMBEDDINGS GENERATED"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()