from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.character import (
    CharacterChunkingStrategy,
)
from backend.rag.ingestion.document import Document


def main() -> None:

    document = Document(
        id="test_document",
        content=(
            "This is a simple test document. "
            "We will use it to test the chunking "
            "process. The document contains enough "
            "text to generate multiple chunks."
        ),
        metadata={
            "source": "test.md",
            "document_type": "test",
        },
    )

    strategy = CharacterChunkingStrategy()

    chunker = Chunker(
        strategy=strategy,
        chunk_size=50,
        chunk_overlap=10,
    )

    chunks = chunker.chunk(document)

    print(
        f"Document: {document.id}"
    )

    print(
        f"Chunks generated: {len(chunks)}"
    )

    for chunk in chunks:

        print("\n" + "=" * 60)

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
            f"Text: "
            f"{chunk.text}"
        )


if __name__ == "__main__":
    main()