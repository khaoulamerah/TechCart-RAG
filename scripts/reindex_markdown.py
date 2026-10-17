from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from backend.rag.data_pipelines.pipeline import Pipeline
from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.load import LoadStage
from backend.rag.data_pipelines.stages.save import SaveStage
from backend.rag.data_pipelines.stages.validate import ValidateStage
from backend.rag.data_pipelines.utils import DataType
from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.ingestion.chunker import Chunker
from backend.rag.ingestion.chunking.markdown import (
    MarkdownChunkingStrategy,
)
from backend.rag.ingestion.document import (
    Chunk,
    Document,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]

SOURCE_DIR = (
    PROJECT_ROOT
    / "data"
    / "semi_structured"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "markdown"
)

CHUNKS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "chunks"
    / "markdown_chunks.json"
)

EMBEDDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings"
    / "markdown_embeddings_bge_m3.json"
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "bge-m3",
)

QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "qdrant",
)

QDRANT_PORT = int(
    os.getenv(
        "QDRANT_PORT",
        "6333",
    )
)

QDRANT_COLLECTION = os.getenv(
    "QDRANT_COLLECTION",
    "techcart_bge_m3",
)


def collect_markdown_files() -> list[str]:
    """Collect all Markdown source files."""

    files = sorted(
        SOURCE_DIR.rglob("*.md")
    )

    if not files:
        raise FileNotFoundError(
            f"No Markdown files found in {SOURCE_DIR}"
        )

    return [
        str(path)
        for path in files
    ]


def run_data_pipeline(
    files: list[str],
) -> None:
    """Run Load → Clean → Validate → Derive → Save."""

    print("\n" + "=" * 70)
    print("STEP 1 - DATA PIPELINE")
    print("=" * 70)

    pipeline = Pipeline(
        stages=[
            LoadStage(),
            CleanStage(),
            ValidateStage(),
            DeriveStage(),
            SaveStage(),
        ]
    )

    pipeline.set_datatype(
        DataType.MD
    )

    pipeline.run(files)


def load_documents() -> list[Document]:
    """Load processed Markdown documents."""

    print("\n" + "=" * 70)
    print("STEP 2 - LOAD PROCESSED DOCUMENTS")
    print("=" * 70)

    documents: list[Document] = []

    for path in sorted(
        PROCESSED_DIR.glob("*.md")
    ):
        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            continue

        documents.append(
            Document(
                id=path.stem,
                content=content,
                metadata={
                    "source": str(
                        path.relative_to(
                            PROJECT_ROOT
                        )
                    ),
                    "document_type": "markdown",
                },
            )
        )

    if not documents:
        raise ValueError(
            "No processed Markdown documents found."
        )

    print(
        f"Documents loaded: {len(documents)}"
    )

    return documents


def chunk_documents(
    documents: list[Document],
) -> list[Chunk]:
    """Run structured Markdown chunking."""

    print("\n" + "=" * 70)
    print("STEP 3 - CHUNKING")
    print("=" * 70)

    strategy = MarkdownChunkingStrategy(
        chunk_size=1000,
    )

    chunker = Chunker(
        strategy=strategy,
    )

    all_chunks: list[Chunk] = []

    for document in documents:
        chunks = chunker.chunk(
            document
        )

        print(
            f"{document.id}: "
            f"{len(chunks)} chunks"
        )

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(
            "Chunking produced no chunks."
        )

    CHUNKS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = [
        {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
        }
        for chunk in all_chunks
    ]

    CHUNKS_FILE.write_text(
        json.dumps(
            serialized,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Total chunks: {len(all_chunks)}"
    )

    print(
        f"Saved to: {CHUNKS_FILE}"
    )

    return all_chunks


def generate_embeddings(
    chunks: list[Chunk],
) -> list[list[float]]:
    """Generate BGE-M3 embeddings through Ollama."""

    print("\n" + "=" * 70)
    print("STEP 4 - EMBEDDINGS")
    print("=" * 70)

    embedder = OllamaEmbeddingStrategy(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    texts = [
        chunk.text
        for chunk in chunks
    ]

    print(
        f"Generating embeddings for "
        f"{len(texts)} chunks..."
    )

    embeddings = embedder.embed(
        texts
    )

    if len(embeddings) != len(chunks):
        raise RuntimeError(
            "Embedding count does not match "
            "chunk count."
        )

    vector_dimension = len(
        embeddings[0]
    )

    print(
        f"Vector dimension: "
        f"{vector_dimension}"
    )

    EMBEDDINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized_embeddings: list[
        dict[str, Any]
    ] = []

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        serialized_embeddings.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "embedding": embedding,
            }
        )

    output = {
        "model_name": "bge_m3",
        "ollama_model": EMBEDDING_MODEL,
        "vector_dimension": vector_dimension,
        "num_embeddings": len(embeddings),
        "embeddings": serialized_embeddings,
    }

    EMBEDDINGS_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Saved to: {EMBEDDINGS_FILE}"
    )

    return embeddings


def create_point_id(
    chunk_id: str,
) -> str:
    """Create a deterministic Qdrant point ID."""

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
        )
    )


def index_qdrant(
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> None:
    """Recreate and populate the Qdrant collection."""

    print("\n" + "=" * 70)
    print("STEP 5 - QDRANT")
    print("=" * 70)

    if not embeddings:
        raise ValueError(
            "No embeddings to index."
        )

    vector_dimension = len(
        embeddings[0]
    )

    store = QdrantVectorStore(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=QDRANT_COLLECTION,
    )

    print(
        f"Collection: {QDRANT_COLLECTION}"
    )

    print(
        "Recreating collection..."
    )

    store.recreate_collection(
        vector_size=vector_dimension
    )

    ids: list[str] = []
    vectors: list[list[float]] = []
    payloads: list[dict[str, Any]] = []

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        ids.append(
            create_point_id(chunk.id)
        )

        vectors.append(
            embedding
        )

        payloads.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }
        )

    batch_size = 32

    for start in range(
        0,
        len(ids),
        batch_size,
    ):
        end = start + batch_size

        store.upsert(
            ids=ids[start:end],
            vectors=vectors[start:end],
            payloads=payloads[start:end],
        )

        print(
            f"Indexed "
            f"{min(end, len(ids))}/"
            f"{len(ids)} points."
        )

    # Verify search
    results = store.search(
        query_vector=embeddings[0],
        limit=1,
    )

    if not results:
        raise RuntimeError(
            "Qdrant indexing completed but "
            "verification search returned no results."
        )

    print(
        "Qdrant verification: OK"
    )


def main() -> None:
    print("\n" + "=" * 70)
    print("TECHCART - FULL MARKDOWN REINDEX")
    print("=" * 70)

    files = collect_markdown_files()

    print(
        f"Source files: {len(files)}"
    )

    run_data_pipeline(
        files
    )

    documents = load_documents()

    chunks = chunk_documents(
        documents
    )

    embeddings = generate_embeddings(
        chunks
    )

    index_qdrant(
        chunks,
        embeddings,
    )

    print("\n" + "=" * 70)
    print("FULL REINDEX COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()