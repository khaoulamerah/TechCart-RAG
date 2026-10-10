
from abc import ABC, abstractmethod
from typing import Any


class Reranker(ABC):

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
