from backend.rag.ingestion.chunking.base import ChunkingStrategy
from backend.rag.ingestion.document import Chunk, Document


class Chunker:

    def __init__(
        self,
        strategy: ChunkingStrategy,
    ) -> None:
        self.strategy = strategy

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:

        return self.strategy.chunk(document)