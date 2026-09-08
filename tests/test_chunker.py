from pathlib import Path

from backend.config.settings import settings
from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.character import (
    CharacterChunkingStrategy,
)
from backend.rag.ingestion.document import Document


MARKDOWN_FILES: list[str] = [
    "data/processed/markdown/faq.md",
    "data/processed/markdown/gpu_buying_guide.md",
    "data/processed/markdown/payment_policy.md",
    "data/processed/markdown/return_policy.md",
    "data/processed/markdown/shipping_policy.md",
    "data/processed/markdown/store_info.md",
    "data/processed/markdown/warranty_policy.md",
]


def load_document(file_path: str) -> Document:
    """Load one Markdown file and create a Document object."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Markdown file not found: {file_path}"
        )

    content: str = path.read_text(encoding="utf-8")

    document = Document(
        id=path.stem,
        content=content,
        metadata={
            "source": file_path,
            "document_type": path.parent.name,
        },
    )

    return document


def main() -> None:

    print("=" * 60)
    print("MARKDOWN CHUNKING TEST")
    print("=" * 60)

    print(f"Chunk size: {settings.CHUNK_SIZE}")
    print(f"Chunk overlap: {settings.CHUNK_OVERLAP}")

    strategy = CharacterChunkingStrategy()

    chunker = Chunker(
        strategy=strategy,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    total_chunks: int = 0

    for file_path in MARKDOWN_FILES:

        print("\n" + "=" * 60)
        print(f"Processing: {file_path}")
        print("=" * 60)

        document = load_document(file_path)

        print(f"Document ID: {document.id}")
        print(f"Document type: {document.metadata['document_type']}")
        print(f"Content length: {len(document.content)} characters")

        chunks = chunker.chunk(document)

        print(f"Chunks generated: {len(chunks)}")

        total_chunks += len(chunks)

        for chunk in chunks:

            print("\n" + "-" * 60)

            print(f"Chunk ID: {chunk.id}")

            print(
                f"Document ID: "
                f"{chunk.document_id}"
            )

            print(
                f"Position: "
                f"{chunk.metadata['position']}"
            )

            print(
                f"Source: "
                f"{chunk.metadata['source']}"
            )

            print(
                f"Text:\n"
                f"{chunk.text}"
            )

    print("\n" + "=" * 60)
    print("CHUNKING SUMMARY")
    print("=" * 60)

    print(f"Documents processed: {len(MARKDOWN_FILES)}")
    print(f"Total chunks generated: {total_chunks}")


if __name__ == "__main__":
    main()