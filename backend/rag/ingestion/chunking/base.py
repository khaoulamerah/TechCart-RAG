from abc import ABC, abstractmethod

from backend.rag.ingestion.document import Chunk, Document


class ChunkingStrategy(ABC):

    @abstractmethod
    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:
        raise NotImplementedError