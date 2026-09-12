from backend.rag.ingestion.chunking.base import ChunkingStrategy
from backend.rag.ingestion.document import Chunk, Document


class CharacterChunkingStrategy(ChunkingStrategy):

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than "
                "chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:

        chunks: list[Chunk] = []

        step = self.chunk_size - self.chunk_overlap

        start = 0
        position = 0

        while start < len(document.content):

            end = start + self.chunk_size

            text = document.content[start:end].strip()

            if text:
                chunks.append(
                    Chunk(
                        id=(
                            f"{document.id}_"
                            f"chunk_{position:04d}"
                        ),
                        document_id=document.id,
                        text=text,
                        metadata={
                            **document.metadata,
                            "position": position,
                        },
                    )
                )

            start += step
            position += 1

        return chunks