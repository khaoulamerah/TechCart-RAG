from backend.rag.ingestion.chunking.base import (
    ChunkingStrategy,
)
from backend.rag.ingestion.document import (
    Chunk,
    Document,
)


class Chunker:

    def __init__(
        self,
        strategy: ChunkingStrategy,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
    ) -> None:

        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:

        return self.strategy.chunk(
            document=document,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )