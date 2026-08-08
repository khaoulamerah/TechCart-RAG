from __future__ import annotations

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger("techcart.embedder")


class EmbeddingError(Exception):
    """Raised when Ollama embedding generation fails after retries."""


class OllamaEmbedder:


    def __init__(
        self,
        base_url: str,
        model: str,
        batch_size: int = 16,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._batch_size = batch_size
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._expected_dim: Optional[int] = None

    # ─── API publique ───────────────────────────────────────────────

    async def aembed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            vectors = await self._embed_with_retry(batch)
            all_vectors.extend(vectors)
            logger.info(
                "Embedding : %d/%d textes encodés",
                min(start + self._batch_size, len(texts)), len(texts),
            )
        return all_vectors

    async def aembed_query(self, text: str) -> list[float]:
        vectors = await self.aembed_batch([text])
        return vectors[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return asyncio.run(self.aembed_batch(texts))

    # ─── Détails d'implémentation ───────────────────────────────────

    async def _embed_with_retry(self, batch: list[str]) -> list[list[float]]:
        last_error: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        f"{self._base_url}/api/embed",
                        json={"model": self._model, "input": batch},
                    )
                response.raise_for_status()
                payload = response.json()
                vectors = payload.get("embeddings")
                if not vectors:
                    raise EmbeddingError(
                        f"Réponse Ollama inattendue (pas de champ 'embeddings'): {payload}"
                    )
                self._validate_dimensions(vectors)
                return vectors

            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_error = exc
                wait_seconds = 2 ** (attempt - 1)
                logger.warning(
                    "Ollama injoignable (tentative %d/%d) : %s — nouvel essai dans %ds",
                    attempt, self._max_retries, exc, wait_seconds,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(wait_seconds)

            except httpx.HTTPStatusError as exc:
                raise EmbeddingError(
                    f"Ollama a répondu {exc.response.status_code} : {exc.response.text}. "
                    f"As-tu bien exécuté `ollama pull {self._model}` ?"
                ) from exc

        raise EmbeddingError(
            f"Impossible de joindre Ollama ({self._base_url}) après "
            f"{self._max_retries} tentatives : {last_error}"
        )

    def _validate_dimensions(self, vectors: list[list[float]]) -> None:
        for vector in vectors:
            dim = len(vector)
            if self._expected_dim is None:
                self._expected_dim = dim
                logger.info("Dimension d'embedding détectée : %d", dim)
            elif dim != self._expected_dim:
                raise EmbeddingError(
                    f"Dimension d'embedding incohérente : {dim} reçu, "
                    f"{self._expected_dim} attendu. Le modèle Ollama a-t-il "
                    "changé en cours d'exécution ?"
                )


# ─────────────────────────────────────────────────────────────────────
# Test manuel rapide (voir section "comment tester" de l'explication)
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")

    embedder = OllamaEmbedder(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
    )

    try:
        vectors = embedder.embed_batch([
            "GeForce RTX 4090 — carte graphique Nvidia haut de gamme.",
            "Intel i7-7Y75 — processeur basse consommation pour ultrabook.",
        ])
        print(f"\n{len(vectors)} vecteurs générés, dimension {len(vectors[0])}")
        print("Premiers éléments du 1er vecteur :", vectors[0][:5])
    except EmbeddingError as exc:
        print(f"\nÉchec attendu si Ollama n'est pas démarré localement : {exc}")
        sys.exit(1)