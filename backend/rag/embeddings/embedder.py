import ollama

from backend.rag.embeddings.base import EmbeddingStrategy


class OllamaEmbeddingStrategy(EmbeddingStrategy):

    def __init__(self, model: str) -> None:

        if not model:
            raise ValueError("model cannot be empty.")

        self.model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = ollama.embed(
            model=self.model,
            input=texts,
        )

        embeddings = response["embeddings"]

        if len(embeddings) != len(texts):
            raise ValueError(
                f"Expected {len(texts)} embeddings, "
                f"but received {len(embeddings)}."
            )

        return embeddings