"""RAG retriever package with lazy factory import."""

from backend.rag.retriever.retriever import Retriever


def get_retriever() -> Retriever:
    """Build or return the cached production retriever on demand."""
    from backend.rag.retriever.factory import get_retriever as get_factory_retriever

    return get_factory_retriever()


__all__ = ["Retriever", "get_retriever"]
