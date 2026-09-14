import json
from pathlib import Path

from backend.rag.embeddings.embedder import OllamaEmbeddingStrategy


CHUNKS_FILE = Path("data/processed/chunks/markdown_chunks.json")
OUTPUT_FILE = Path("data/processed/embeddings/markdown_embeddings.json")


def load_chunks(file_path: Path) -> list[dict]:
    """Load chunks from the JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {file_path}"
        )

    with file_path.open("r", encoding="utf-8") as file:
        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError("Chunks JSON must contain a list.")

    return chunks


def save_embeddings(
    file_path: Path,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> None:
    """Save chunks and their embeddings to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    data = []

    for chunk, embedding in zip(chunks, embeddings):
        data.append(
            {
                "id": chunk["id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": embedding,
            }
        )

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def main() -> None:
    print(f"Loading chunks from: {CHUNKS_FILE}")

    chunks = load_chunks(CHUNKS_FILE)

    print(f"Number of chunks: {len(chunks)}")

    texts = [chunk["text"] for chunk in chunks]

    embedder = OllamaEmbeddingStrategy(
        model="nomic-embed-text",
    )

    print("Generating embeddings...")

    embeddings = embedder.embed(texts)

    if len(embeddings) != len(chunks):
        raise ValueError(
            "Number of embeddings does not match number of chunks."
        )

    vector_dimension = len(embeddings[0])

    print(f"Number of embeddings: {len(embeddings)}")
    print(f"Vector dimension: {vector_dimension}")

    print("\nFirst 3 chunks:")

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):
        if index >= 3:
            break

        print(f"\nChunk {index}:")
        print(f"ID: {chunk['id']}")
        print(f"Text: {chunk['text'][:150]}...")
        print(f"Vector dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

    save_embeddings(
        OUTPUT_FILE,
        chunks,
        embeddings,
    )

    print(f"\nEmbeddings saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()