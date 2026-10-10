from __future__ import annotations

from time import perf_counter
from typing import Any

from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.reranker.base import Reranker
from backend.rag.vector_store.qdrant import QdrantVectorStore


class Retriever:
    """Two-stage retrieval pipeline with optional observability data.

    Question
        ↓
    Embedding
        ↓
    Qdrant vector search
        ↓
    retrieval_k candidates
        ↓
    Reranking
        ↓
    top_k documents
    """

    def __init__(
        self,
        embedder: OllamaEmbeddingStrategy,
        vector_store: QdrantVectorStore,
        reranker: Reranker | None = None,
        retrieval_k: int = 20,
        top_k: int = 5,
    ) -> None:
        if retrieval_k <= 0:
            raise ValueError("retrieval_k must be greater than zero.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        if retrieval_k < top_k:
            raise ValueError(
                "retrieval_k must be greater than or equal to top_k."
            )

        self.embedder = embedder
        self.vector_store = vector_store
        self.reranker = reranker
        self.retrieval_k = retrieval_k
        self.top_k = top_k

    @staticmethod
    def _document_trace(document: dict[str, Any]) -> dict[str, Any]:
        payload = document.get("payload") or {}
        return {
            "chunk_id": str(payload.get("chunk_id", document.get("id", "unknown"))),
            "document": payload.get("document_id"),
            "text": str(payload.get("text", "")),
            "vector_score": document.get("score"),
            "bm25_score": document.get("bm25_score"),
            "hybrid_score": document.get("hybrid_score"),
        }

    def retrieve_with_trace(
        self,
        query: str,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Retrieve documents and return data suitable for RAG observability."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        cleaned_query = query.strip()

        retrieval_started = perf_counter()

        embedding_started = perf_counter()
        query_embedding = self.embedder.embed([cleaned_query])[0]
        embedding_latency_ms = (perf_counter() - embedding_started) * 1000

        vector_started = perf_counter()
        candidates = self.vector_store.search(
            query_vector=query_embedding,
            limit=self.retrieval_k,
        )
        vector_latency_ms = (perf_counter() - vector_started) * 1000

        retrieval_latency_ms = (perf_counter() - retrieval_started) * 1000

        retrieval_trace = {
            "embedding_model": self.embedder.model,
            "top_k": self.retrieval_k,
            "latency_ms": retrieval_latency_ms,
            "documents": [
                self._document_trace(document)
                for document in candidates
            ],
            "embedding_latency_ms": embedding_latency_ms,
            "vector_search_latency_ms": vector_latency_ms,
        }

        if not candidates:
            return [], {
                "retrieval": retrieval_trace,
                "reranking": None,
            }

        if self.reranker is None:
            final_documents = candidates[: self.top_k]
            return final_documents, {
                "retrieval": retrieval_trace,
                "reranking": None,
            }

        reranking_started = perf_counter()
        final_documents = self.reranker.rerank(
            query=cleaned_query,
            documents=candidates,
            top_k=self.top_k,
        )
        reranking_latency_ms = (perf_counter() - reranking_started) * 1000

        reranking_trace = {
            "model": getattr(
                self.reranker,
                "model_name",
                type(self.reranker).__name__,
            ),
            "input_count": len(candidates),
            "output_count": len(final_documents),
            "latency_ms": reranking_latency_ms,
            "documents": [
                {
                    **self._document_trace(document),
                    "original_score": document.get("score"),
                    "rerank_score": document.get("rerank_score"),
                }
                for document in final_documents
            ],
        }

        return final_documents, {
            "retrieval": retrieval_trace,
            "reranking": reranking_trace,
        }

    def retrieve(self, query: str) -> list[dict[str, Any]]:
        documents, _ = self.retrieve_with_trace(query)
        return documents
