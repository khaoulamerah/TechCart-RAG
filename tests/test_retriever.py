from backend.rag.retriever.factory import (
    get_retriever,
)


def main() -> None:
    retriever = get_retriever()

    question = (
        "What is the return policy?"
    )

    results = retriever.retrieve(
        question
    )

    print()
    print("=" * 80)
    print("RETRIEVER TEST")
    print("=" * 80)

    print(
        f"Question: {question}"
    )

    print(
        f"Results: {len(results)}"
    )

    for index, result in enumerate(
        results,
        start=1,
    ):
        payload = result["payload"]

        print()
        print(
            f"Result {index}"
        )

        print(
            f"Score: "
            f"{result['score']:.4f}"
        )

        print(
            f"Document: "
            f"{payload.get('document_id')}"
        )

        print(
            f"Chunk: "
            f"{payload.get('chunk_id')}"
        )

        print(
            f"Text: "
            f"{payload.get('text', '')[:300]}"
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()