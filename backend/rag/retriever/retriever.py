from typing import Any

from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


class Retriever:

    def __init__(
        self,
        embedder: OllamaEmbeddingStrategy,
        vector_store: QdrantVectorStore,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
    ) -> None:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        if similarity_threshold < 0:
            raise ValueError(
                "similarity_threshold cannot be negative."
            )

        self.embedder = embedder
        self.vector_store = vector_store
        self.top_k = top_k
        self.similarity_threshold = (
            similarity_threshold
        )

    def retrieve(
        self,
        query: str,
    ) -> list[dict[str, Any]]:

        cleaned_query = query.strip()

        if not cleaned_query:
            raise ValueError(
                "query cannot be empty."
            )

        # 1. Convert question into BGE-M3 vector

        query_embedding = self.embedder.embed(
            [cleaned_query]
        )[0]

        # BGE-M3 should produce 1024 dimensions.
        if len(query_embedding) != 1024:
            raise ValueError(
                "BGE-M3 query embedding must have "
                f"1024 dimensions, got "
                f"{len(query_embedding)}."
            )

        # 2. Search Qdrant
        results = self.vector_store.search(
            query_vector=query_embedding,
            limit=self.top_k,
        )

        # 3. Apply similarity threshold

        filtered_results = [
            result
            for result in results
            if result["score"]
            >= self.similarity_threshold
        ]

        return filtered_results