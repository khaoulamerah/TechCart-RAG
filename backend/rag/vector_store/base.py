from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    """Abstract interface for a vector store."""

    @abstractmethod
    def create_collection(self, vector_size: int) -> None:
        """Create the vector collection."""
        raise NotImplementedError

    @abstractmethod
    def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict[str, Any]],
    ) -> None:
        """Insert or update vectors and their payloads."""
        raise NotImplementedError

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search for the most similar vectors."""
        raise NotImplementedError