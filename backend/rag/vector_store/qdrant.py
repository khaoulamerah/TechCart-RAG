from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from backend.rag.vector_store.base import VectorStore


class QdrantVectorStore(VectorStore):
    """Vector store implementation using Qdrant."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "techcart_products",
    ) -> None:
        self.client = QdrantClient(
            host=host,
            port=port,
        )
        self.collection_name = collection_name

    def create_collection(self, vector_size: int) -> None:
        """Create the Qdrant collection if it does not exist."""

        collections = self.client.get_collections()

        collection_names = [
            collection.name
            for collection in collections.collections
        ]

        if self.collection_name in collection_names:
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Insert or update vectors and their payloads."""

        if not (
            len(ids)
            == len(vectors)
            == len(payloads)
        ):
            raise ValueError(
                "ids, vectors and payloads must have the same length."
            )

        points = [
            PointStruct(
                id=chunk_id,
                vector=vector,
                payload=payload,
            )
            for chunk_id, vector, payload in zip(
                ids,
                vectors,
                payloads,
            )
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for the most similar vectors."""

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results.points
        ]