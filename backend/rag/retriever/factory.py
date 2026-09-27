from functools import lru_cache

from backend.config.settings import settings
from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.retriever.retriever import Retriever
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


@lru_cache
def get_retriever() -> Retriever:

    embedder = OllamaEmbeddingStrategy(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    vector_store = QdrantVectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION,
    )

    return Retriever(
        embedder=embedder,
        vector_store=vector_store,
        top_k=settings.TOP_K_RESULTS,
        similarity_threshold=(
            settings.SIMILARITY_THRESHOLD
        ),
    )