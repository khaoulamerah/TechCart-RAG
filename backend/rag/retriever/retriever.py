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
    """
    Two-stage retrieval pipeline.

    Stage 1:
        Question
            ↓
        BGE-M3 embedding
            ↓
        Qdrant
            ↓
        top retrieval_k candidates

    Stage 2:
        BGE reranker
            ↓
        top_k final documents
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

    def warmup(self) -> None:
        """
        Warm up the complete retrieval pipeline.

        This method intentionally runs synchronously
        because it is called through asyncio.to_thread()
        during FastAPI startup.
        """

        query = (
            "What is the return policy?"
        )

        # BGE-M3 embedding
        query_embedding = self.embedder.embed(
            [query]
        )[0]

        # Qdrant retrieval
        candidates = self.vector_store.search(
            query_vector=query_embedding,
            limit=self.retrieval_k,
        )

        if not candidates:
            raise RuntimeError(
                "Retriever warm-up failed: "
                "Qdrant returned no candidates."
            )

        # BGE reranker
        if self.reranker is not None:
            reranked = self.reranker.rerank(
                query=query,
                documents=candidates,
                top_k=self.top_k,
            )

            if not reranked:
                raise RuntimeError(
                    "Retriever warm-up failed: "
                    "reranker returned no documents."
                )

    def retrieve(
        self,
        query: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve and rerank documents.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        cleaned_query = query.strip()

        # ─────────────────────────────────────────
        # 1. BGE-M3 query embedding
        # ─────────────────────────────────────────

        query_embedding = self.embedder.embed(
            [cleaned_query]
        )[0]

        # ─────────────────────────────────────────
        # 2. Qdrant first-stage retrieval
        # ─────────────────────────────────────────

        candidates = self.vector_store.search(
            query_vector=query_embedding,
            limit=self.retrieval_k,
        )

        if not candidates:
            return []

        # ─────────────────────────────────────────
        # 3. BGE reranking
        # ─────────────────────────────────────────

        if self.reranker is not None:
            return self.reranker.rerank(
                query=cleaned_query,
                documents=candidates,
                top_k=self.top_k,
            )

        # Fallback without reranker
        return candidates[: self.top_k]

