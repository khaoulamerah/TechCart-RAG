import json
import uuid
from pathlib import Path
from typing import Any

from backend.rag.embeddings.models import (
    QDRANT_COLLECTIONS,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


EMBEDDINGS_DIR = Path(
    "data/processed/embeddings"
)


def load_embeddings(
    file_path: Path,
) -> dict[str, Any]:
    """Load embeddings from a JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError(
            "Embeddings JSON must contain an object."
        )

    if "embeddings" not in data:
        raise ValueError(
            "Embeddings JSON must contain "
            "an 'embeddings' field."
        )

    if not isinstance(
        data["embeddings"],
        list,
    ):
        raise ValueError(
            "'embeddings' must contain a list."
        )

    if not data["embeddings"]:
        raise ValueError(
            "Embeddings list cannot be empty."
        )

    return data


def create_point_id(
    chunk_id: str,
) -> str:
    """
    Create a deterministic UUID for a chunk.

    The same chunk ID always produces
    the same Qdrant point ID.
    """

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
        )
    )


def create_payload(
    item: dict[str, Any],
) -> dict[str, Any]:
    """Create the Qdrant payload for one chunk."""

    return {
        "chunk_id": item["id"],
        "text": item["text"],
        "document_id": item["document_id"],
        "metadata": item["metadata"],
    }


def index_model(
    model_name: str,
    embeddings_file: Path,
) -> None:
    """Create and populate one Qdrant collection."""

    print("\n" + "=" * 70)
    print(f"MODEL: {model_name}")
    print(f"FILE: {embeddings_file}")
    print("=" * 70)

    data = load_embeddings(
        embeddings_file
    )

    embeddings = data["embeddings"]

    vector_size = data["vector_dimension"]

    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Vector size: "
        f"{vector_size}"
    )

    collection_name = QDRANT_COLLECTIONS[
        model_name
    ]

    print(
        f"Qdrant collection: "
        f"{collection_name}"
    )

    store = QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name=collection_name,
    )

    print("Creating collection...")

    store.create_collection(
        vector_size=vector_size,
    )

    print("Collection ready.")

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

    print(
        f"Upserting "
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

    print("\nTesting search...")

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
        payload = result["payload"]

        print(
            f"\nResult {index}"
        )

        print(
            f"Qdrant ID: "
            f"{result['id']}"
        )

        print(
            f"Chunk ID: "
            f"{payload['chunk_id']}"
        )

        print(
            f"Score: "
            f"{result['score']}"
        )

        print(
            f"Text: "
            f"{payload['text'][:200]}..."
        )


def main() -> None:
    """Index all embedding models into Qdrant."""

    print(
        "Starting Qdrant indexing..."
    )

    print(
        f"Models to index: "
        f"{len(QDRANT_COLLECTIONS)}"
    )

    for model_name in QDRANT_COLLECTIONS:
        embeddings_file = (
            EMBEDDINGS_DIR
            / f"markdown_embeddings_{model_name}.json"
        )

        index_model(
            model_name=model_name,
            embeddings_file=embeddings_file,
        )

    print("\n" + "=" * 70)
    print("ALL MODELS INDEXED SUCCESSFULLY")
    print("=" * 70)

    print("\nQdrant collections:")

    for collection_name in (
        QDRANT_COLLECTIONS.values()
    ):
        print(
            f"  - {collection_name}"
        )


if __name__ == "__main__":
    main()