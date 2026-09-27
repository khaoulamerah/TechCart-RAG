from ollama import Client

from backend.rag.embeddings.base import EmbeddingStrategy


class OllamaEmbeddingStrategy(EmbeddingStrategy):

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
    ) -> None:

        if not model:
            raise ValueError(
                "model cannot be empty."
            )

        if not base_url:
            raise ValueError(
                "base_url cannot be empty."
            )

        self.model = model
        self.base_url = base_url

        self.client = Client(
            host=base_url,
        )

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        if not texts:
            return []

        response = self.client.embed(
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