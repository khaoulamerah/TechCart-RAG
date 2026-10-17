"""HTTP client for the standalone reranker service."""

from __future__ import annotations

import math
from typing import Any

import httpx

from backend.rag.reranker.base import Reranker


class RerankerServiceError(RuntimeError):
    """Raised when the remote reranker is unavailable or returns invalid data."""


class HttpReranker(Reranker):
    """Call the reranker HTTP API and map returned indexes to original Qdrant hits."""

    def __init__(
        self,
        base_url: str,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        timeout_seconds: float = 150.0,
        max_document_chars: int = 12000,
    ) -> None:
        if not base_url or not base_url.strip():
            raise ValueError("Reranker base_url cannot be empty.")
        if timeout_seconds <= 0:
            raise ValueError("Reranker timeout must be positive.")
        if max_document_chars <= 0:
            raise ValueError("max_document_chars must be positive.")

        self.base_url = base_url.rstrip("/")
        self.model_name = model_name.strip() or "Qwen/Qwen3-Reranker-0.6B"
        self.timeout_seconds = float(timeout_seconds)
        self.max_document_chars = int(max_document_chars)
        self._client = httpx.Client(timeout=httpx.Timeout(self.timeout_seconds))

    def warm_up(self) -> None:
        """Verify that the remote model has loaded and passed its warm-up."""
        try:
            response = self._client.get(f"{self.base_url}/health/ready")
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("status") != "ready":
                raise RerankerServiceError(
                    f"Reranker service is not ready: {payload!r}"
                )
        except RerankerServiceError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise RerankerServiceError(
                f"Unable to reach ready endpoint at {self.base_url}: {exc}"
            ) from exc

    @staticmethod
    def _document_text(document: dict[str, Any]) -> str:
        payload = document.get("payload") or {}
        value = payload.get("text")
        if not isinstance(value, str):
            value = document.get("text", "")
        return value.strip() if isinstance(value, str) else ""

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

        request_documents: list[dict[str, Any]] = []
        original_documents: dict[int, dict[str, Any]] = {}
        empty_documents: dict[int, dict[str, Any]] = {}

        for index, document in enumerate(documents):
            text = self._document_text(document)
            if not text:
                empty_documents[index] = document
                continue
            request_documents.append(
                {
                    "index": index,
                    "text": text[: self.max_document_chars],
                }
            )
            original_documents[index] = document

        remote_results: list[dict[str, Any]] = []
        if request_documents:
            try:
                response = self._client.post(
                    f"{self.base_url}/rerank",
                    json={
                        "query": query.strip(),
                        "documents": request_documents,
                        "top_k": min(top_k, len(request_documents)),
                    },
                )
                response.raise_for_status()
                payload = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise RerankerServiceError(
                    f"Reranker request to {self.base_url}/rerank failed: {exc}"
                ) from exc

            results = payload.get("results") if isinstance(payload, dict) else None
            if not isinstance(results, list):
                raise RerankerServiceError(
                    "Reranker API response must contain a 'results' list."
                )
            expected_count = min(top_k, len(request_documents))
            if len(results) != expected_count:
                raise RerankerServiceError(
                    "Reranker returned an unexpected result count: "
                    f"expected {expected_count}, received {len(results)}."
                )

            seen_indexes: set[int] = set()
            for item in results:
                if not isinstance(item, dict):
                    raise RerankerServiceError("Reranker result must be an object.")
                index = item.get("index")
                score = item.get("score")
                if (
                    not isinstance(index, int)
                    or index not in original_documents
                    or index in seen_indexes
                ):
                    raise RerankerServiceError(
                        f"Reranker returned an invalid or duplicate document index: {index!r}."
                    )
                if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
                    raise RerankerServiceError(
                        f"Reranker returned an invalid score for document index {index}."
                    )
                seen_indexes.add(index)
                ranked_document = dict(original_documents[index])
                ranked_document["rerank_score"] = float(score)
                remote_results.append(ranked_document)

        # Documents with no usable text cannot be scored; keep them at the end
        # with score zero only if needed to fill top_k.
        for index, document in empty_documents.items():
            ranked_document = dict(document)
            ranked_document["rerank_score"] = 0.0
            remote_results.append(ranked_document)

        remote_results.sort(
            key=lambda document: float(document.get("rerank_score", 0.0)),
            reverse=True,
        )
        return remote_results[:top_k]

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()
