from functools import lru_cache

from backend.config.settings import settings
from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.reranker.bge import (
    BGEReranker,
)
from backend.rag.retriever.retriever import (
    Retriever,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    """
    Build and cache the complete retrieval pipeline.

    BGE-M3
        ↓
    Qdrant
        ↓
    BGE Reranker
        ↓
    Top-K
    """
    print("EMMMMMMMMMMMMMMbider")
    embedder = (
        OllamaEmbeddingStrategy(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
    )

    print("Vvvvvvvvvvvvvvvvvvector store")
    vector_store = QdrantVectorStore(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        collection_name=(
            settings.QDRANT_COLLECTION
        ),
    )

    print("Rrrrrrrrrrrrrreranker")
    reranker = BGEReranker(
        model_name=settings.RERANKER_MODEL,
        use_fp16=settings.RERANKER_USE_FP16,
    )
    print("Retrieeeeeeeeeeeever")
    r =  Retriever(
        embedder=embedder,
        vector_store=vector_store,
        reranker=reranker,
        retrieval_k=settings.RETRIEVAL_K,
        top_k=settings.TOP_K_RESULTS,
    )   
    print("Retrieeeeeeeeeeeever done")
    return r