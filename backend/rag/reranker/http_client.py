from __future__ import annotations

import logging
from typing import Any

import httpx

from backend.rag.reranker.base import Reranker

logger = logging.getLogger("techcart.reranker.http")


class HttpReranker(Reranker):
    """Call the dedicated reranker service, falling back to vector ranking.

    A model download or inference failure must not make the entire RAG chat
    unavailable. If the HTTP service is not ready, the original retrieval
    scores are used to select the best candidates instead.
    """

    def __init__(
        self,
        base_url: str = "http://reranker:8001",
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("base_url cannot be empty.")
        if not model_name or not model_name.strip():
            raise ValueError("model_name cannot be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip()
        self.timeout_seconds = float(timeout_seconds)

    @staticmethod
    def _fallback(
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Keep vector-search order when the external reranker is unavailable."""
        ranked = sorted(
            documents,
            key=lambda document: float(document.get("score") or 0.0),
            reverse=True,
        )
        return ranked[:top_k]

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        if not documents:
            return []

        timeout = httpx.Timeout(
            self.timeout_seconds,
            connect=min(5.0, self.timeout_seconds),
            write=min(10.0, self.timeout_seconds),
            pool=min(5.0, self.timeout_seconds),
        )

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(
                    f"{self.base_url}/rerank",
                    json={
                        "query": query.strip(),
                        "documents": documents,
                        "top_k": top_k,
                    },
                )
                response.raise_for_status()
                body = response.json()
                ranked_documents = body.get("documents")
                if not isinstance(ranked_documents, list):
                    raise ValueError(
                        "Reranker response must contain a 'documents' list."
                    )
                return ranked_documents[:top_k]

        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            logger.warning(
                "Reranker service is unavailable (%s). Falling back to vector scores.",
                exc,
            )
            return self._fallback(documents, top_k)
