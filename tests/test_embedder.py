from backend.rag.embeddings.embedder import OllamaEmbeddingStrategy


def main() -> None:
    embedder = OllamaEmbeddingStrategy(
        model="nomic-embed-text",
    )

    texts = [
        "Do you accept PayPal?",
        "TechCart accepts Visa, Mastercard and PayPal.",
        "How long does shipping take?",
    ]

    embeddings = embedder.embed(texts)

    print(f"Number of texts: {len(texts)}")
    print(f"Number of embeddings: {len(embeddings)}")

    for index, embedding in enumerate(embeddings):
        print(f"\nText {index}:")
        print(texts[index])

        print(f"Vector dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    main()