import json
from pathlib import Path
from typing import Any

from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.markdown import (
    MarkdownChunkingStrategy,
)
from backend.rag.ingestion.document import Chunk, Document


# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]

MARKDOWN_DIR = (
    PROJECT_ROOT
    / "data"/ "processed"/ "markdown"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"/ "processed"/ "chunks"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "markdown_chunks.json"
)


# Load Markdown documents
def load_markdown_documents() -> list[Document]:

    documents: list[Document] = []

    markdown_files = sorted(
        MARKDOWN_DIR.glob("*.md")
    )

    if not markdown_files:
        raise FileNotFoundError(
            f"No Markdown files found in: "
            f"{MARKDOWN_DIR}"
        )

    for file_path in markdown_files:

        content = file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            print(
                f"Skipping empty file: "
                f"{file_path.name}"
            )
            continue

        document = Document(
            id=file_path.stem,
            content=content,
            metadata={
                "source": str(
                    file_path.relative_to(
                        PROJECT_ROOT
                    )
                ),
                "document_type": "markdown",
            },
        )

        documents.append(document)

    return documents


# Save chunks

def save_chunks(
    chunks: list[Chunk],
) -> None:
    """
    Save generated chunks to JSON.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chunks_data: list[dict[str, Any]] = []

    for chunk in chunks:

        chunks_data.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
        )

    OUTPUT_FILE.write_text(
        json.dumps(
            chunks_data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )


def main() -> None:

    print("=" * 70)
    print("MARKDOWN STRUCTURED CHUNKING TEST")
    print("=" * 70)

    # Load documents
    documents = load_markdown_documents()

    print()
    print(
        f"Documents loaded: {len(documents)}"
    )

    # Create strategy
    strategy = MarkdownChunkingStrategy(
        chunk_size=1000,
    )

    # Create Chunker
    chunker = Chunker(
        strategy=strategy,
    )

    # Process documents
    all_chunks: list[Chunk] = []

    for document in documents:

        print()
        print("=" * 70)
        print(
            f"Document: {document.id}"
        )
        print(
            f"Source: "
            f"{document.metadata['source']}"
        )
        print("=" * 70)

        chunks = chunker.chunk(
            document
        )

        print(
            f"Chunks generated: {len(chunks)}"
        )

        for chunk in chunks:

            print()
            print("-" * 70)

            print(
                f"ID: {chunk.id}"
            )

            print(
                f"Position: "
                f"{chunk.metadata['position']}"
            )

            print(
                f"Length: "
                f"{len(chunk.text)} characters"
            )

            print()

            print(chunk.text)

        all_chunks.extend(chunks)

    # Save results
    save_chunks(all_chunks)



if __name__ == "__main__":
    main()

