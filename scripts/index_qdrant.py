from __future__ import annotations

import json
from pathlib import Path

from backend.config.settings import settings
from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.ingestion.indexer import (
    QdrantIndexer,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks"
    / "markdown_chunks.json"
)


def load_chunks() -> list[dict]:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {CHUNKS_FILE}"
        )

    with CHUNKS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError(
            "Chunks JSON must contain a list."
        )

    return chunks


def main() -> None:

    print("=" * 70)
    print("TECHCART - QDRANT INDEXING")
    print("=" * 70)

    chunks = load_chunks()

    print(
        f"Chunks loaded: {len(chunks)}"
    )

    print(
        f"Embedding model: "
        f"{settings.EMBEDDING_MODEL}"
    )

    print(
        f"Qdrant collection: "
        f"{settings.QDRANT_COLLECTION}"
    )

    embedder = OllamaEmbeddingStrategy(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    vector_store = QdrantVectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION,
    )

    indexer = QdrantIndexer(
        embedder=embedder,
        vector_store=vector_store,
        batch_size=16,
    )

    total = indexer.index(
        chunks
    )

    print("=" * 70)
    print(
        f"Successfully indexed {total} chunks."
    )
    print("=" * 70)


if __name__ == "__main__":
    main()