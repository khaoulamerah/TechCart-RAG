import json
from pathlib import Path
from typing import Any


QUESTIONS_FILE = Path(
    "tests/evaluation/retrieval_questions.json"
)


def load_questions(
    file_path: Path = QUESTIONS_FILE,
) -> list[dict[str, Any]]:
    """Load retrieval evaluation questions."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Questions file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        questions = json.load(file)

    if not isinstance(questions, list):
        raise ValueError(
            "Questions JSON must contain a list."
        )

    if not questions:
        raise ValueError(
            "Questions dataset is empty."
        )

    for question in questions:
        if "id" not in question:
            raise ValueError(
                "Each question must contain 'id'."
            )

        if "question" not in question:
            raise ValueError(
                "Each question must contain 'question'."
            )

        if "relevant_documents" not in question:
            raise ValueError(
                "Each question must contain "
                "'relevant_documents'."
            )

    return questions