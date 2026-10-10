from functools import lru_cache

from backend.config.settings import settings
from backend.rag.embeddings.embedder import OllamaEmbeddingStrategy
from backend.rag.reranker.ollama_qwen import OllamaQwenReranker
from backend.rag.retriever.retriever import Retriever
from backend.rag.vector_store.qdrant import QdrantVectorStore


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    """Create and cache the RAG retriever."""
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
        if provider != "ollama":
            raise ValueError(
                f"Unsupported RERANKER_PROVIDER '{settings.RERANKER_PROVIDER}'. "
                "This version supports 'ollama'."
            )

        reranker = OllamaQwenReranker(
            model_name=settings.RERANKER_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            timeout_seconds=settings.RERANKER_TIMEOUT_SECONDS,
            top_logprobs=settings.RERANKER_TOP_LOGPROBS,
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
