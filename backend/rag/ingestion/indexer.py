from __future__ import annotations

import uuid
from typing import Any

from backend.rag.embeddings.base import EmbeddingStrategy
from backend.rag.vector_store.qdrant import QdrantVectorStore


class QdrantIndexer:

    def __init__(
        self,
        embedder: EmbeddingStrategy,
        vector_store: QdrantVectorStore,
        batch_size: int = 16,
    ) -> None:

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero."
            )

        self.embedder = embedder
        self.vector_store = vector_store
        self.batch_size = batch_size

    @staticmethod
    def create_point_id(
        chunk_id: str,
    ) -> str:

        return str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                chunk_id,
            )
        )

    @staticmethod
    def create_payload(
        chunk: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "chunk_id": chunk["id"],
            "document_id": chunk["document_id"],
            "text": chunk["text"],
            "metadata": chunk.get(
                "metadata",
                {},
            ),
        }

    def index(
        self,
        chunks: list[dict[str, Any]],
    ) -> int:

        if not chunks:
            raise ValueError(
                "Cannot index an empty chunk list."
            )

        total = 0

        for start in range(
            0,
            len(chunks),
            self.batch_size,
        ):

            batch = chunks[
                start : start + self.batch_size
            ]

            texts = [
                chunk["text"]
                for chunk in batch
            ]

            embeddings = self.embedder.embed(
                texts
            )

            if len(embeddings) != len(batch):
                raise RuntimeError(
                    "Embedding count does not match "
                    "chunk count."
                )

            if not embeddings:
                continue

            vector_size = len(
                embeddings[0]
            )

            if start == 0:
                self.vector_store.create_collection(
                    vector_size=vector_size
                )

            ids = [
                self.create_point_id(
                    chunk["id"]
                )
                for chunk in batch
            ]

            payloads = [
                self.create_payload(
                    chunk
                )
                for chunk in batch
            ]

            self.vector_store.upsert(
                ids=ids,
                vectors=embeddings,
                payloads=payloads,
            )

            total += len(batch)

            print(
                f"Indexed {total}/{len(chunks)} chunks."
            )

        return total