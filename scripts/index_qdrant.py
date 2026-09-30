from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from backend.rag.vector_store.qdrant import (  # noqa: E402
    QdrantVectorStore,
)


EMBEDDINGS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "embeddings"
)


MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "bge-m3",
)

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "techcart_bge_m3",
)

QDRANT_HOST = os.getenv(
    "QDRANT_HOST",
    "localhost",
)

QDRANT_PORT = int(
    os.getenv(
        "QDRANT_PORT",
        "6333",
    )
)


EMBEDDINGS_FILE = (
    EMBEDDINGS_DIR
    / "markdown_embeddings_bge_m3.json"
)


def load_embeddings(
    file_path: Path,
) -> dict[str, Any]:
    """Load precomputed embeddings from JSON."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: "
            f"{file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Embeddings JSON must contain "
            "an object."
        )

    embeddings = data.get(
        "embeddings"
    )

    if not isinstance(
        embeddings,
        list,
    ):
        raise ValueError(
            "Embeddings JSON must contain "
            "an 'embeddings' list."
        )

    if not embeddings:
        raise ValueError(
            "Embeddings list cannot be empty."
        )

    vector_dimension = data.get(
        "vector_dimension"
    )

    if not isinstance(
        vector_dimension,
        int,
    ):
        raise ValueError(
            "Missing or invalid "
            "'vector_dimension'."
        )

    return data


def create_point_id(
    chunk_id: str,
) -> str:

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
        )
    )


def create_payload(
    item: dict[str, Any],
) -> dict[str, Any]:

    required_fields = (
        "id",
        "text",
        "document_id",
    )

    for field in required_fields:

        if field not in item:
            raise ValueError(
                f"Embedding item is missing "
                f"required field: {field}"
            )

    return {
        "chunk_id": item["id"],
        "text": item["text"],
        "document_id": item["document_id"],
        "metadata": item.get(
            "metadata",
            {},
        ),
    }


def index_embeddings() -> None:
    """Create and populate the configured Qdrant collection."""

    print("\n" + "=" * 70)
    print("TECHCART - QDRANT INDEXING")
    print("=" * 70)

    print(
        f"Embedding model: {MODEL_NAME}"
    )

    print(
        f"Embeddings file: "
        f"{EMBEDDINGS_FILE}"
    )

    print(
        f"Qdrant host: "
        f"{QDRANT_HOST}"
    )

    print(
        f"Qdrant port: "
        f"{QDRANT_PORT}"
    )

    print(
        f"Collection: "
        f"{COLLECTION_NAME}"
    )

    data = load_embeddings(
        EMBEDDINGS_FILE
    )

    embeddings = data[
        "embeddings"
    ]

    vector_dimension = data[
        "vector_dimension"
    ]

    print(
        f"\nNumber of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Vector dimension: "
        f"{vector_dimension}"
    )

    store = QdrantVectorStore(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=COLLECTION_NAME,
    )

    # ---------------------------------------------------------
    # Create collection
    # ---------------------------------------------------------

    print(
        "\nCreating Qdrant collection..."
    )

    store.create_collection(
        vector_size=vector_dimension,
    )

    print(
        "Collection ready."
    )

    # ---------------------------------------------------------
    # Prepare points
    # ---------------------------------------------------------

    ids = [
        create_point_id(
            item["id"]
        )
        for item in embeddings
    ]

    vectors = [
        item["embedding"]
        for item in embeddings
    ]

    payloads = [
        create_payload(item)
        for item in embeddings
    ]

    # ---------------------------------------------------------
    # Validate vectors
    # ---------------------------------------------------------

    for index, vector in enumerate(
        vectors
    ):

        if len(vector) != vector_dimension:
            raise ValueError(
                f"Invalid vector dimension "
                f"at index {index}: "
                f"expected {vector_dimension}, "
                f"got {len(vector)}"
            )

    # ---------------------------------------------------------
    # Upsert
    # ---------------------------------------------------------

    print(
        f"\nUpserting "
        f"{len(vectors)} points..."
    )

    store.upsert(
        ids=ids,
        vectors=vectors,
        payloads=payloads,
    )

    print(
        f"Successfully inserted "
        f"{len(vectors)} points."
    )

    # ---------------------------------------------------------
    # Verify search
    # ---------------------------------------------------------

    print(
        "\nTesting vector search..."
    )

    query_vector = vectors[0]

    results = store.search(
        query_vector=query_vector,
        limit=5,
    )

    print(
        f"Search returned "
        f"{len(results)} results."
    )

    for index, result in enumerate(
        results,
        start=1,
    ):

        payload = result.get(
            "payload",
            {},
        )

        print(
            f"\nResult {index}"
        )

        print(
            f"Qdrant ID: "
            f"{result.get('id')}"
        )

        print(
            f"Chunk ID: "
            f"{payload.get('chunk_id')}"
        )

        print(
            f"Score: "
            f"{result.get('score')}"
        )

        text = payload.get(
            "text",
            "",
        )

        print(
            f"Text: "
            f"{text[:200]}..."
        )

    print("\n" + "=" * 70)
    print("QDRANT INDEXING COMPLETED")
    print("=" * 70)


def main() -> None:
    index_embeddings()


if __name__ == "__main__":
    main()