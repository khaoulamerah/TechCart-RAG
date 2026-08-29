from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger("techcart.rag.chunker")


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

GPU_JSON = PROCESSED_DIR / "gpus.json"
CPU_JSON = PROCESSED_DIR / "cpus.json"


# ============================================================
# CHUNK CONFIGURATION
# ============================================================

DEFAULT_CHUNK_SIZE = 1200
DEFAULT_CHUNK_OVERLAP = 150


# ============================================================
# CHUNK MODEL
# ============================================================

@dataclass(slots=True)
class Chunk:
    """
    Represents one text chunk prepared for embedding.

    The chunker is intentionally independent from:
    - embedding models
    - Qdrant
    - MongoDB
    - FastAPI
    """

    id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """
    Normalize whitespace without changing the semantic content.
    """

    if not text:
        return ""

    return " ".join(text.split())


# ============================================================
# GENERIC TEXT CHUNKING
# ============================================================

def split_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split text into overlapping chunks.

    This implementation is intentionally simple for the
    initial RAG pipeline.

    Later, this can be replaced by:
        RecursiveCharacterTextSplitter
    or another more advanced strategy.
    """

    text = clean_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    step = chunk_size - chunk_overlap

    while start < text_length:
        end = min(start + chunk_size, text_length)

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start += step

    return chunks


# ============================================================
# JSON LOADING
# ============================================================

def load_json_records(path: Path) -> list[dict[str, Any]]:
    """
    Load a JSON file containing a list of product records.
    """

    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            f"Expected a JSON list in {path}, "
            f"got {type(data).__name__}."
        )

    records: list[dict[str, Any]] = []

    for index, record in enumerate(data):
        if not isinstance(record, dict):
            logger.warning(
                "Skipping invalid record at index %d in %s",
                index,
                path,
            )
            continue

        records.append(record)

    logger.info(
        "Loaded %d records from %s",
        len(records),
        path,
    )

    return records


# ============================================================
# ENGLISH GPU TEXT
# ============================================================

def build_gpu_text(record: dict[str, Any]) -> str:
    """
    Convert one GPU record into English text.

    The resulting text is designed for semantic embeddings.
    """

    parts: list[str] = []

    name = record.get("name", "Unknown GPU")
    manufacturer = record.get(
        "manufacturer",
        "Unknown manufacturer",
    )

    parts.append(
        f"{name} is a graphics processing unit (GPU) "
        f"manufactured by {manufacturer}."
    )

    if record.get("architecture"):
        parts.append(
            f"It uses the {record['architecture']} architecture."
        )

    if record.get("is_notebook_gpu"):
        parts.append(
            "This is a notebook GPU designed for laptop computers "
            "and is not sold as a standalone desktop graphics card."
        )

    if record.get("release_date"):
        parts.append(
            f"The release date was {record['release_date']}."
        )

    memory_parts: list[str] = []

    if record.get("memory_gb") is not None:
        memory_parts.append(
            f"{record['memory_gb']} GB"
        )

    if record.get("memory_type"):
        memory_parts.append(
            str(record["memory_type"])
        )

    if memory_parts:
        memory_text = (
            "The GPU has "
            + " ".join(memory_parts)
            + " of memory"
        )

        if record.get("memory_bus_bit") is not None:
            memory_text += (
                f" with a {int(record['memory_bus_bit'])}-bit memory bus"
            )

        if record.get("memory_bandwidth_gb_s") is not None:
            memory_text += (
                f" and a memory bandwidth of "
                f"{record['memory_bandwidth_gb_s']} GB/s"
            )

        memory_text += "."

        parts.append(memory_text)

    clock_parts: list[str] = []

    if record.get("core_clock_mhz") is not None:
        clock_parts.append(
            f"a core clock of {record['core_clock_mhz']} MHz"
        )

    if record.get("boost_clock_mhz") is not None:
        clock_parts.append(
            f"a boost clock of {record['boost_clock_mhz']} MHz"
        )

    if clock_parts:
        parts.append(
            "The GPU operates with "
            + " and ".join(clock_parts)
            + "."
        )

    if record.get("max_power_watts") is not None:
        parts.append(
            f"The maximum power consumption is "
            f"{record['max_power_watts']} watts."
        )

    if record.get("process_nm") is not None:
        parts.append(
            f"The manufacturing process is "
            f"{record['process_nm']} nm."
        )

    if record.get("best_resolution"):
        parts.append(
            f"The maximum supported resolution is "
            f"{record['best_resolution']}."
        )

    api_parts: list[str] = []

    if record.get("direct_x"):
        api_parts.append(
            f"DirectX {record['direct_x']}"
        )

    if record.get("open_gl"):
        api_parts.append(
            f"OpenGL {record['open_gl']}"
        )

    if api_parts:
        parts.append(
            "Supported graphics APIs include "
            + ", ".join(api_parts)
            + "."
        )

    if not record.get("specs_available", True):
        parts.append(
            "Detailed technical specifications are not available "
            "for this product. Only pricing information is known."
        )

    if record.get("reference_price_usd") is not None:
        parts.append(
            f"The reference price is "
            f"${record['reference_price_usd']}."
        )

    if record.get("store_price_eur") is not None:
        price = record["store_price_eur"]

        if record.get("store_stock", 0) > 0:
            stock = record["store_stock"]

            parts.append(
                f"The product is available at TechCart for "
                f"€{price}, with {stock} unit(s) currently in stock."
            )
        else:
            parts.append(
                f"The product is listed at TechCart for "
                f"€{price}, but it is currently out of stock."
            )

    return clean_text(" ".join(parts))


# ============================================================
# ENGLISH GPU METADATA
# ============================================================

def build_gpu_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:

    metadata: dict[str, Any] = {
        "product_id": str(record["id"]),
        "category": "gpu",
        "name": record.get("name"),
        "manufacturer": record.get("manufacturer"),
        "in_stock": int(record.get("store_stock", 0)) > 0,
        "store_stock": int(record.get("store_stock", 0)),
        "store_price_eur": float(
            record.get("store_price_eur", 0)
        ),
    }

    if record.get("architecture"):
        metadata["architecture"] = record["architecture"]

    if record.get("release_date"):
        metadata["release_date"] = record["release_date"]

    if record.get("memory_gb") is not None:
        metadata["memory_gb"] = float(
            record["memory_gb"]
        )

    if record.get("reference_price_usd") is not None:
        metadata["reference_price_usd"] = float(
            record["reference_price_usd"]
        )

    return metadata


# ============================================================
# ENGLISH CPU TEXT
# ============================================================

def build_cpu_text(record: dict[str, Any]) -> str:
    """
    Convert one CPU record into English semantic text.
    """

    parts: list[str] = []

    name = record.get("name", "Unknown CPU")

    parts.append(
        f"{name} is an Intel central processing unit (CPU)."
    )

    if record.get("product_collection"):
        parts.append(
            f"It belongs to the {record['product_collection']} "
            "product family."
        )

    if record.get("vertical_segment"):
        parts.append(
            f"It targets the {record['vertical_segment']} "
            "market segment."
        )

    if record.get("status"):
        parts.append(
            f"The product status is {record['status']}."
        )

    core_parts: list[str] = []

    if record.get("cores") is not None:
        core_parts.append(
            f"{record['cores']} CPU cores"
        )

    if record.get("threads") is not None:
        core_parts.append(
            f"{record['threads']} threads"
        )

    if core_parts:
        parts.append(
            "It has "
            + " and ".join(core_parts)
            + "."
        )

    frequency_parts: list[str] = []

    if record.get("base_frequency_ghz") is not None:
        frequency_parts.append(
            f"a base frequency of "
            f"{record['base_frequency_ghz']} GHz"
        )

    if record.get("max_turbo_ghz") is not None:
        frequency_parts.append(
            f"a maximum turbo frequency of "
            f"{record['max_turbo_ghz']} GHz"
        )

    if frequency_parts:
        parts.append(
            "The processor operates with "
            + " and ".join(frequency_parts)
            + "."
        )

    if record.get("cache"):
        parts.append(
            f"The processor has {record['cache']} of cache."
        )

    if record.get("tdp_watts") is not None:
        parts.append(
            f"The thermal design power (TDP) is "
            f"{record['tdp_watts']} watts."
        )

    if record.get("lithography_nm") is not None:
        parts.append(
            f"The lithography process is "
            f"{record['lithography_nm']} nm."
        )

    if record.get("launch_quarter"):
        parts.append(
            f"The processor was launched in "
            f"{record['launch_quarter']}."
        )

    if record.get("recommended_price_usd") is not None:
        parts.append(
            f"The recommended Intel price was "
            f"${record['recommended_price_usd']}."
        )

    if record.get("store_price_eur") is not None:
        price = record["store_price_eur"]

        if record.get("store_stock", 0) > 0:
            stock = record["store_stock"]

            parts.append(
                f"The processor is available at TechCart for "
                f"€{price}, with {stock} unit(s) currently in stock."
            )
        else:
            parts.append(
                f"The processor is listed at TechCart for "
                f"€{price}, but it is currently out of stock."
            )

    return clean_text(" ".join(parts))


# ============================================================
# CPU METADATA
# ============================================================

def build_cpu_metadata(
    record: dict[str, Any],
) -> dict[str, Any]:

    metadata: dict[str, Any] = {
        "product_id": str(record["id"]),
        "category": "cpu",
        "name": record.get("name"),
        "manufacturer": "Intel",
        "in_stock": int(record.get("store_stock", 0)) > 0,
        "store_stock": int(record.get("store_stock", 0)),
        "store_price_eur": float(
            record.get("store_price_eur", 0)
        ),
    }

    if record.get("product_collection"):
        metadata["product_collection"] = (
            record["product_collection"]
        )

    if record.get("vertical_segment"):
        metadata["vertical_segment"] = (
            record["vertical_segment"]
        )

    if record.get("status"):
        metadata["status"] = record["status"]

    if record.get("cores") is not None:
        metadata["cores"] = int(record["cores"])

    if record.get("threads") is not None:
        metadata["threads"] = int(record["threads"])

    if record.get("tdp_watts") is not None:
        metadata["tdp_watts"] = float(
            record["tdp_watts"]
        )

    if record.get("launch_quarter"):
        metadata["launch_quarter"] = (
            record["launch_quarter"]
        )

    return metadata


# ============================================================
# GENERIC RECORD -> CHUNKS
# ============================================================

def build_chunks_from_records(
    records: Iterable[dict[str, Any]],
    *,
    category: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:

    chunks: list[Chunk] = []

    for record in records:

        product_id = str(record["id"])

        if category == "gpu":
            document_text = build_gpu_text(record)
            metadata = build_gpu_metadata(record)

        elif category == "cpu":
            document_text = build_cpu_text(record)
            metadata = build_cpu_metadata(record)

        else:
            raise ValueError(
                f"Unsupported category: {category}"
            )

        text_chunks = split_text(
            document_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for position, text in enumerate(text_chunks):

            chunk_id = (
                f"{category}_{product_id}_{position}"
            )

            chunk_metadata = {
                **metadata,
                "document_id": product_id,
                "chunk_id": chunk_id,
                "chunk_position": position,
                "chunk_count": len(text_chunks),
                "source": "techcart_products",
                "language": "en",
            }

            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=text,
                    metadata=chunk_metadata,
                )
            )

    return chunks


# ============================================================
# REAL DATA LOADER
# ============================================================

def load_product_records() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:

    gpu_records = load_json_records(GPU_JSON)
    cpu_records = load_json_records(CPU_JSON)

    return gpu_records, cpu_records


# ============================================================
# COMPLETE CHUNKING PIPELINE
# ============================================================

def build_all_chunks(
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:

    gpu_records, cpu_records = load_product_records()

    gpu_chunks = build_chunks_from_records(
        gpu_records,
        category="gpu",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    cpu_chunks = build_chunks_from_records(
        cpu_records,
        category="cpu",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = gpu_chunks + cpu_chunks

    logger.info(
        "Chunking completed: %d products -> %d chunks",
        len(gpu_records) + len(cpu_records),
        len(chunks),
    )

    return chunks


# ============================================================
# MANUAL TEST
# ============================================================

def main() -> None:

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    chunks = build_all_chunks()

    print()
    print("=" * 70)
    print("CHUNKING TEST")
    print("=" * 70)

    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        print("No chunks generated.")
        return

    for chunk in chunks[:3]:

        print()
        print("-" * 70)

        print(f"Chunk ID:")
        print(chunk.id)

        print()
        print("Text:")
        print(chunk.text)

        print()
        print("Metadata:")
        print(json.dumps(
            chunk.metadata,
            indent=2,
            ensure_ascii=False,
        ))


if __name__ == "__main__":
    main()