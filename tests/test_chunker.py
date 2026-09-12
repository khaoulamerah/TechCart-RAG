from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.chonkie import (
    ChonkieSemanticChunkingStrategy,
)
from backend.rag.ingestion.document import Document


def main() -> None:

    document = Document(
        id="test_document",
        content=(
            """
            The RTX 4070 is a graphics card based on
            the Ada Lovelace architecture. It has 12 GB
            of GDDR6X memory and is suitable for gaming
            and artificial intelligence workloads.

            The TechCart store provides several delivery
            options for customers. Standard delivery
            usually takes between three and five business
            days. Customers can track their orders from
            their account.

            Customers can pay using Visa, Mastercard,
            or other supported payment methods.
            """
        ),
        metadata={
            "source": "test.md",
            "document_type": "test",
        },
    )

    strategy = ChonkieSemanticChunkingStrategy(
        chunk_size=512,
    )

    chunker = Chunker(
        strategy=strategy,
    )

    chunks = chunker.chunk(document)

    print(
        f"Document: {document.id}"
    )

    print(
        f"Chunks generated: {len(chunks)}"
    )

    for chunk in chunks:

        print("\n" + "=" * 70)

        print(f"ID: {chunk.id}")

        print(
            f"Document ID: "
            f"{chunk.document_id}"
        )

        print(
            f"Position: "
            f"{chunk.metadata['position']}"
        )

        print(
            f"Text:\n{chunk.text}"
        )


if __name__ == "__main__":
    main()