from chonkie import SemanticChunker

from backend.rag.ingestion.chunking.base import ChunkingStrategy
from backend.rag.ingestion.document import Chunk, Document


class ChonkieSemanticChunkingStrategy(ChunkingStrategy):

    def __init__(
        self,
        chunk_size: int = 512,
    ) -> None:
        self.chunk_size = chunk_size

        self.chunker = SemanticChunker(
            chunk_size=chunk_size,
        )

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:

        chonkie_chunks = self.chunker(
            document.content
        )

        chunks: list[Chunk] = []

        for position, chonkie_chunk in enumerate(
            chonkie_chunks
        ):
            chunks.append(
                Chunk(
                    id=(
                        f"{document.id}_"
                        f"chunk_{position:04d}"
                    ),
                    document_id=document.id,
                    text=chonkie_chunk.text,
                    metadata={
                        **document.metadata,
                        "position": position,
                    },
                )
            )

        return chunks