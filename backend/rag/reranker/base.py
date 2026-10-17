from abc import ABC, abstractmethod
from typing import Any


class Reranker(ABC):
    """Common interface implemented by TechCart reranking strategies."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Return up to ``top_k`` documents ranked by query relevance."""
        raise NotImplementedError
