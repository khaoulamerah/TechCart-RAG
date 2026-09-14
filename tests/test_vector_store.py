import json
import uuid
from pathlib import Path

from backend.rag.vector_store.qdrant import QdrantVectorStore


EMBEDDINGS_FILE = Path(
    "data/processed/embeddings/markdown_embeddings.json"
)


def load_embeddings(file_path: Path) -> list[dict]:
    """Load embeddings from JSON."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "Embeddings JSON must contain a list."
        )

    return data


def create_point_id(chunk_id: str) -> str:
    """Create a deterministic UUID for a chunk."""

    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            chunk_id,
        )
    )


def main() -> None:
    print("Loading embeddings...")

    data = load_embeddings(EMBEDDINGS_FILE)

    print(f"Number of embeddings: {len(data)}")

    vector_size = len(data[0]["embedding"])

    print(f"Vector size: {vector_size}")

    store = QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name="techcart_products",
    )

    print("Creating Qdrant collection...")

    store.create_collection(
        vector_size=vector_size,
    )

    print("Collection ready.")

    ids = [
        create_point_id(item["id"])
        for item in data
    ]

    vectors = [
        item["embedding"]
        for item in data
    ]

    payloads = [
        {
            "chunk_id": item["id"],
            "text": item["text"],
            "document_id": item["document_id"],
            "metadata": item["metadata"],
        }
        for item in data
    ]

    print("Upserting points...")

    store.upsert(
        ids=ids,
        vectors=vectors,
        payloads=payloads,
    )

    print(f"Inserted {len(ids)} points.")

    print("\nTesting search...")

    query_vector = data[0]["embedding"]

    results = store.search(
        query_vector=query_vector,
        limit=5,
    )

    for index, result in enumerate(results):
        print(f"\nResult {index + 1}")
        print(f"Qdrant ID: {result['id']}")
        print(f"Chunk ID: {result['payload']['chunk_id']}")
        print(f"Score: {result['score']}")
        print(
            f"Text: {result['payload']['text'][:200]}..."
        )


if __name__ == "__main__":
    main()