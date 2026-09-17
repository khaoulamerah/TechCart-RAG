import json
from pathlib import Path

from backend.rag.embeddings.embedder import OllamaEmbeddingStrategy
from backend.rag.embeddings.models import EMBEDDING_MODELS


CHUNKS_FILE = Path(
    "data/processed/chunks/markdown_chunks.json"
)

OUTPUT_DIR = Path(
    "data/processed/embeddings"
)


def load_chunks(file_path: Path) -> list[dict]:
    """Load chunks from the JSON file."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Chunks file not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        chunks = json.load(file)

    if not isinstance(chunks, list):
        raise ValueError(
            "Chunks JSON must contain a list."
        )

    if not chunks:
        raise ValueError(
            "Chunks JSON is empty."
        )

    return chunks


def save_embeddings(
    file_path: Path,
    chunks: list[dict],
    embeddings: list[list[float]],
    model_name: str,
    ollama_model: str,
) -> None:
    """Save chunks and their embeddings to a JSON file."""

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks does not match "
            "number of embeddings."
        )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = []

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        data.append(
            {
                "id": chunk["id"],
                "document_id": chunk["document_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": embedding,
            }
        )

    output = {
        "model_name": model_name,
        "ollama_model": ollama_model,
        "vector_dimension": len(embeddings[0]),
        "num_embeddings": len(embeddings),
        "embeddings": data,
    }

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )


def generate_embeddings(
    chunks: list[dict],
    model_name: str,
    ollama_model: str,
) -> list[list[float]]:
    """Generate embeddings for all chunks using one model."""

    print("\n" + "=" * 60)
    print(f"Model: {model_name}")
    print(f"Ollama model: {ollama_model}")
    print("=" * 60)

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embedder = OllamaEmbeddingStrategy(
        model=ollama_model,
    )

    print(
        f"Generating embeddings for "
        f"{len(texts)} chunks..."
    )

    embeddings = embedder.embed(texts)

    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Model '{model_name}' returned "
            f"{len(embeddings)} embeddings for "
            f"{len(chunks)} chunks."
        )

    vector_dimension = len(
        embeddings[0]
    )

    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Vector dimension: "
        f"{vector_dimension}"
    )

    print("\nFirst chunk:")

    print(
        f"ID: {chunks[0]['id']}"
    )

    print(
        f"Text: "
        f"{chunks[0]['text'][:150]}..."
    )

    print(
        f"Embedding dimension: "
        f"{len(embeddings[0])}"
    )

    print(
        f"First 5 values: "
        f"{embeddings[0][:5]}"
    )

    return embeddings


def main() -> None:
    print(
        f"Loading chunks from: "
        f"{CHUNKS_FILE}"
    )

    chunks = load_chunks(
        CHUNKS_FILE
    )

    print(
        f"Number of chunks: "
        f"{len(chunks)}"
    )

    print(
        f"\nModels to test: "
        f"{len(EMBEDDING_MODELS)}"
    )

    for model_name, ollama_model in (
        EMBEDDING_MODELS.items()
    ):
        embeddings = generate_embeddings(
            chunks=chunks,
            model_name=model_name,
            ollama_model=ollama_model,
        )

        output_file = (
            OUTPUT_DIR
            / f"markdown_embeddings_{model_name}.json"
        )

        save_embeddings(
            file_path=output_file,
            chunks=chunks,
            embeddings=embeddings,
            model_name=model_name,
            ollama_model=ollama_model,
        )

        print(
            f"\nSaved to: {output_file}"
        )

    print("\n" + "=" * 60)
    print("ALL EMBEDDING MODELS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()