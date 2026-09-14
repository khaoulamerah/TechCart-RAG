import ollama

from backend.rag.embeddings.base import EmbeddingStrategy


class OllamaEmbeddingStrategy(EmbeddingStrategy):

    def __init__(self, model: str = "nomic-embed-text") -> None:
        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = ollama.embed(
            model=self.model,
            input=texts,
        )

        return response["embeddings"]