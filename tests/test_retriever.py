from backend.rag.embeddings.embedder import (
    OllamaEmbeddingStrategy,
)
from backend.rag.reranker.ollama_qwen import (
    OllamaQwenReranker,
)
from backend.rag.vector_store.qdrant import (
    QdrantVectorStore,
)
from backend.rag.retriever.retriever import (
    Retriever,
)


OLLAMA_BASE_URL = "http://localhost:11434"

EMBEDDING_MODEL = "bge-m3"

COLLECTION_NAME = "techcart_bge_m3"

RETRIEVAL_K = 10
TOP_K = 5


def main() -> None:
    """Test BGE-M3 retrieval with the Ollama Qwen3 reranker."""

    print()
    print("=" * 80)
    print("RETRIEVER + RERANKER TEST")
    print("=" * 80)

    embedder = OllamaEmbeddingStrategy(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    vector_store = QdrantVectorStore(
        host="localhost",
        port=6333,
        collection_name=COLLECTION_NAME,
    )

    reranker = OllamaQwenReranker(
        model_name="dengcao/Qwen3-Reranker-0.6B:Q8_0",
        base_url=OLLAMA_BASE_URL,
    )

    retriever = Retriever(
        embedder=embedder,
        vector_store=vector_store,
        reranker=reranker,
        retrieval_k=RETRIEVAL_K,
        top_k=TOP_K,
    )

    question = "What is the return policy?"

    print(f"Question: {question}")
    print()
    print(
        f"Qdrant candidates: {RETRIEVAL_K}"
    )
    print(
        f"Final documents: {TOP_K}"
    )

    results = retriever.retrieve(
        question
    )

    print()
    print(f"Final results: {len(results)}")

    for index, result in enumerate(
        results,
        start=1,
    ):
        payload = result["payload"]

        print()
        print(f"Result {index}")
        print("-" * 80)

        print(
            f"Document: "
            f"{payload.get('document_id')}"
        )

        print(
            f"Chunk: "
            f"{payload.get('chunk_id')}"
        )

        print(
            f"Qdrant score: "
            f"{result.get('score', 0.0):.4f}"
        )

        print(
            f"Rerank score: "
            f"{result.get('rerank_score', 0.0):.4f}"
        )

        text = payload.get(
            "text",
            "",
        )

        print(
            f"Text: {text[:300]}..."
        )

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()