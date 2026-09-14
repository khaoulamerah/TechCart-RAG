from abc import ABC, abstractmethod


class EmbeddingStrategy(ABC):

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError