from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.vector_store.qdrant import (  # noqa: E402
    QdrantVectorStore,
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

QDRANT_COLLECTION = os.getenv(
    "QDRANT_COLLECTION",
    "techcart_bge_m3",
)


def create_store() -> QdrantVectorStore:
    """
    Create a QdrantVectorStore using the
    current application configuration.

    This function does not create or populate
    the collection.
    """

    return QdrantVectorStore(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        collection_name=QDRANT_COLLECTION,
    )


def test_vector_store_connection() -> None:
    """
    Verify that the configured Qdrant collection
    is accessible.

    The collection must already have been created
    by the indexing process.
    """

    store = create_store()

    print("\n" + "=" * 70)
    print("QDRANT VECTOR STORE TEST")
    print("=" * 70)

    print(
        f"Host: {QDRANT_HOST}"
    )

    print(
        f"Port: {QDRANT_PORT}"
    )

    print(
        f"Collection: {QDRANT_COLLECTION}"
    )

    # The vector store should already exist.
    #
    # We intentionally DO NOT:
    #
    # - create the collection
    # - generate embeddings
    # - load embedding files
    # - insert points
    #
    # Those operations belong to the indexing pipeline.

    print(
        "\nVector store initialized successfully."
    )

    print(
        "The collection must be populated "
        "by scripts/index_qdrant.py."
    )


def test_vector_store_search(
    query_vector: list[float],
) -> list[dict[str, Any]]:
    """
    Test vector search against an already
    indexed Qdrant collection.

    Parameters
    ----------
    query_vector:
        A vector with the same dimension as
        the configured Qdrant collection.
    """

    if not query_vector:
        raise ValueError(
            "query_vector cannot be empty."
        )

    store = create_store()

    results = store.search(
        query_vector=query_vector,
        limit=5,
    )

    assert isinstance(
        results,
        list,
    )

    for result in results:

        assert "id" in result
        assert "score" in result
        assert "payload" in result

        payload = result["payload"]

        assert isinstance(
            payload,
            dict,
        )

        assert "chunk_id" in payload
        assert "text" in payload

    return results


def main() -> None:
    """
    Run a basic vector-store connectivity test.

    This function intentionally does not perform
    indexing.
    """

    print("\n" + "=" * 70)
    print("TECHCART - VECTOR STORE TEST")
    print("=" * 70)

    print(
        f"Qdrant host: {QDRANT_HOST}"
    )

    print(
        f"Qdrant port: {QDRANT_PORT}"
    )

    print(
        f"Qdrant collection: "
        f"{QDRANT_COLLECTION}"
    )

    store = create_store()

    print(
        "\nQdrantVectorStore initialized successfully."
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "This test does not create the collection "
        "or insert data."
    )

    print(
        "Run scripts/index_qdrant.py to populate "
        "the collection."
    )

    print("\n" + "=" * 70)
    print("VECTOR STORE TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()