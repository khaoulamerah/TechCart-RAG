from functools import lru_cache

from backend.config.settings import settings
from backend.rag.embeddings.embedder import OllamaEmbeddingStrategy
from backend.rag.reranker.qwen3_transformers import Qwen3TransformersReranker
from backend.rag.retriever.retriever import Retriever
from backend.rag.vector_store.qdrant import QdrantVectorStore


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    """Create and cache the RAG retriever and its configured reranker."""
    embedder = OllamaEmbeddingStrategy(
        model=settings.EMBEDDING_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )

    vector_store = QdrantVectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=settings.QDRANT_COLLECTION,
    )

    reranker = None
    if settings.RERANKER_ENABLED:
        provider = settings.RERANKER_PROVIDER.strip().lower()
        if provider != "transformers":
            raise ValueError(
                f"Unsupported RERANKER_PROVIDER '{settings.RERANKER_PROVIDER}'. "
                "This version supports 'transformers'."
            )

        reranker = Qwen3TransformersReranker(
            model_name=settings.RERANKER_MODEL,
            device=settings.RERANKER_DEVICE,
            max_length=settings.RERANKER_MAX_LENGTH,
            instruction=settings.RERANKER_INSTRUCTION,
            max_document_chars=settings.RERANKER_MAX_DOCUMENT_CHARS,
        )

    return Retriever(
        embedder=embedder,
        vector_store=vector_store,
        reranker=reranker,
        retrieval_k=settings.RETRIEVAL_K,
        top_k=settings.TOP_K_RESULTS,
    )
