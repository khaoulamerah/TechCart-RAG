from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from backend.rag.vector_store.base import VectorStore


class QdrantVectorStore(VectorStore):

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "techcart_products",
    ) -> None:

        if not collection_name:
            raise ValueError(
                "collection_name cannot be empty."
            )

        self.client = QdrantClient(
            host=host,
            port=port,
        )

        self.collection_name = collection_name

    def collection_exists(self) -> bool:
        collections = self.client.get_collections()

        return any(
            collection.name == self.collection_name
            for collection in collections.collections
        )

    def create_collection(
        self,
        vector_size: int,
    ) -> None:

        if vector_size <= 0:
            raise ValueError(
                "vector_size must be greater than 0."
            )

        if self.collection_exists():
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    def delete_collection(self) -> None:
        """Delete the collection if it exists."""

        if self.collection_exists():
            self.client.delete_collection(
                collection_name=self.collection_name
            )

    def recreate_collection(
        self,
        vector_size: int,
    ) -> None:
        """Delete and recreate the collection."""

        self.delete_collection()

        self.create_collection(
            vector_size=vector_size
        )

    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:

        if not (
            len(ids)
            == len(vectors)
            == len(payloads)
        ):
            raise ValueError(
                "ids, vectors and payloads "
                "must have the same length."
            )

        if not ids:
            return

        points = [
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
            for point_id, vector, payload in zip(
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

        if not query_vector:
            raise ValueError(
                "query_vector cannot be empty."
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than 0."
            )

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