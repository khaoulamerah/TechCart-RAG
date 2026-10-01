from typing import Any

from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.reranker.bge import (
    BGEReranker,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


class Retriever:
    """Two-stage retrieval pipeline.

    Question
        ↓
    BGE-M3 embedding
        ↓
    Qdrant
        ↓
    retrieval_k candidates
        ↓
    BGE reranker
        ↓
    top_k documents
    """

    def __init__(
        self,
        embedder: OllamaEmbeddingStrategy,
        vector_store: QdrantVectorStore,
        reranker: BGEReranker | None = None,
        retrieval_k: int = 20,
        top_k: int = 5,
    ) -> None:

        if retrieval_k <= 0:
            raise ValueError(
                "retrieval_k must be greater than zero."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if retrieval_k < top_k:
            raise ValueError(
                "retrieval_k must be greater than "
                "or equal to top_k."
            )

        self.embedder = embedder
        self.vector_store = vector_store
        self.reranker = reranker

        self.retrieval_k = retrieval_k
        self.top_k = top_k

    def retrieve(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """Retrieve and rerank documents."""

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        cleaned_query = query.strip()

        # 1. Embed query
        query_embedding = self.embedder.embed(
            [cleaned_query]
        )[0]

        # 2. Retrieve candidates from Qdrant
        candidates = self.vector_store.search(
            query_vector=query_embedding,
            limit=self.retrieval_k,
        )

        if not candidates:
            return []

        # 3. Rerank candidates
        if self.reranker is not None:
            return self.reranker.rerank(
                query=cleaned_query,
                documents=candidates,
                top_k=self.top_k,
            )

        return candidates[: self.top_k]