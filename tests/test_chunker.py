import json
from pathlib import Path
from typing import Any

from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.semantic import (
    ChonkieSemanticChunkingStrategy,
)
from backend.rag.ingestion.document import Chunk, Document


PROJECT_ROOT = Path(__file__).resolve().parents[1]

MARKDOWN_DIR = (
    PROJECT_ROOT/ "data"/ "processed"/ "markdown"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"/ "processed"/ "chunks"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "semantic_chunks.json"
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

        # Ignore empty files
        if not content:
            print(
                f"Skipping empty file: "
                f"{file_path.name}"
            )
            continue

        # Use filename without .md as document ID
        document_id = file_path.stem

        document = Document(
            id=document_id,
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


# Convert chunks to JSON

def chunks_to_dict(
    chunks: list[Chunk],
) -> list[dict[str, Any]]:

    return [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
        }
        for chunk in chunks
    ]


# Save chunks
def save_chunks(
    chunks: list[Chunk],
) -> None:
    """
    Save generated chunks as JSON.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    chunks_data = chunks_to_dict(chunks)

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
    print("CHUNKS SAVED")
    print("=" * 70)

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    print(
        f"Total chunks: {len(chunks)}"
    )


def main() -> None:

    print("=" * 70)
    print("CHONKIE SEMANTIC CHUNKING TEST")
    print("=" * 70)

    print()
    print(
        f"Markdown directory:"
    )
    print(
        f"  {MARKDOWN_DIR}"
    )

    # Load documents
    documents = load_markdown_documents()

    print()
    print(
        f"Documents loaded: {len(documents)}"
    )

    # Create Chonkie strategy
    strategy = ChonkieSemanticChunkingStrategy(
        chunk_size=512,
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

        chunks = chunker.chunk(document)

        print(
            f"Chunks generated: {len(chunks)}"
        )

        # Display generated chunks

        for chunk in chunks:

            print()
            print("-" * 70)

            print(
                f"ID: {chunk.id}"
            )

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

            print()
            print(
                f"Text:\n{chunk.text}"
            )

        all_chunks.extend(chunks)


    save_chunks(all_chunks)



if __name__ == "__main__":
    main()