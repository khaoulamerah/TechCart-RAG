# from __future__ import annotations

# import json
# import logging
# from dataclasses import dataclass, field
# from pathlib import Path
# from typing import Any

# logger = logging.getLogger("techcart.chunker")

# PROJECT_ROOT = Path(__file__).resolve().parents[3]
# PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
# GPU_JSON = PROCESSED_DIR / "gpus.json"
# CPU_JSON = PROCESSED_DIR / "cpus.json"

# PRICE_SOURCE_LABELS = {
#     "techpowerup_launch_msrp": "prix de lancement (à l'époque)",
#     "tomshardware_current_price": "prix constaté actuellement",
#     "tomshardware_lowest_ever_price": "prix le plus bas jamais constaté",
# }


# @dataclass
# class Chunk:
#     id: str
#     text: str
#     metadata: dict[str, Any] = field(default_factory=dict)


# def _sentence(label: str, *values: str, suffix: str = ".") -> str:
#     return f"{label} : {', '.join(values)}{suffix}"


# def _price_sentence(price_usd: float | None, price_source: str | None) -> str | None:
#     if price_usd is None:
#         return None
#     label = PRICE_SOURCE_LABELS.get(price_source, "prix de référence")
#     return f"{label.capitalize()} : {price_usd} $."


# def _store_sentence(price_eur: float, stock: int) -> str:
#     if stock > 0:
#         return f"Disponible chez TechCart à {price_eur} €, {stock} unité(s) en stock."
#     return (
#         f"Disponible chez TechCart à {price_eur} €, actuellement en rupture de stock."
#     )


# # ─────────────────────────────────────────────────────────────────────
# # Construction des chunks GPU
# # ─────────────────────────────────────────────────────────────────────


# def build_gpu_text(record: dict) -> str:
#     parts: list[str] = [f"{record['name']} — carte graphique {record['manufacturer']}."]

#     if record.get("architecture"):
#         parts.append(_sentence("Architecture", record["architecture"]))

#     if record.get("is_notebook_gpu"):
#         parts.append(
#             "Modèle destiné aux ordinateurs portables (GPU intégré, "
#             "non vendu séparément)."
#         )

#     if record.get("release_date"):
#         parts.append(_sentence("Date de sortie", record["release_date"]))

#     memory_bits = []
#     if record.get("memory_gb") is not None:
#         memory_bits.append(f"{record['memory_gb']} Go")
#     if record.get("memory_type"):
#         memory_bits.append(record["memory_type"])
#     if memory_bits:
#         sentence = "Mémoire : " + " ".join(memory_bits)
#         if record.get("memory_bus_bit") is not None:
#             sentence += f" sur bus {int(record['memory_bus_bit'])} bits"
#         if record.get("memory_bandwidth_gb_s") is not None:
#             sentence += f", bande passante {record['memory_bandwidth_gb_s']} Go/s"
#         parts.append(sentence + ".")

#     clocks = []
#     if record.get("core_clock_mhz") is not None:
#         clocks.append(f"cœur {record['core_clock_mhz']} MHz")
#     if record.get("boost_clock_mhz") is not None:
#         clocks.append(f"boost {record['boost_clock_mhz']} MHz")
#     if clocks:
#         parts.append(_sentence("Fréquences", ", ".join(clocks)))

#     if record.get("max_power_watts") is not None:
#         parts.append(
#             _sentence("Consommation maximale", f"{record['max_power_watts']} W")
#         )

#     if record.get("process_nm") is not None:
#         parts.append(_sentence("Gravure", f"{record['process_nm']} nm"))

#     if record.get("best_resolution"):
#         parts.append(
#             _sentence("Résolution maximale supportée", record["best_resolution"])
#         )

#     apis = []
#     if record.get("direct_x"):
#         apis.append(f"DirectX {record['direct_x']}")
#     if record.get("open_gl"):
#         apis.append(f"OpenGL {record['open_gl']}")
#     if apis:
#         parts.append("Compatible " + ", ".join(apis) + ".")

#     if not record.get("specs_available", True):
#         parts.append(
#             "Fiche technique détaillée non disponible pour ce modèle : "
#             "seules les informations de prix sont connues."
#         )

#     price_sentence = _price_sentence(
#         record.get("reference_price_usd"), record.get("price_source")
#     )
#     if price_sentence:
#         parts.append(price_sentence)

#     parts.append(_store_sentence(record["store_price_eur"], record["store_stock"]))

#     return " ".join(parts)


# def build_gpu_metadata(record: dict) -> dict[str, Any]:
#     metadata: dict[str, Any] = {
#         "id": record["id"],
#         "category": "gpu",
#         "name": record["name"],
#         "manufacturer": record["manufacturer"],
#         "is_notebook_gpu": bool(record.get("is_notebook_gpu") or False),
#         "specs_available": bool(record["specs_available"]),
#         "store_price_eur": float(record["store_price_eur"]),
#         "store_stock": int(record["store_stock"]),
#         "in_stock": record["store_stock"] > 0,
#     }
#     if record.get("memory_gb") is not None:
#         metadata["memory_gb"] = float(record["memory_gb"])
#     if record.get("release_date"):
#         metadata["release_date"] = record["release_date"]
#     if record.get("reference_price_usd") is not None:
#         metadata["reference_price_usd"] = float(record["reference_price_usd"])
#     return metadata


# # ─────────────────────────────────────────────────────────────────────
# # Construction des chunks CPU
# # ─────────────────────────────────────────────────────────────────────
# def build_cpu_text(record: dict) -> str:
#     parts: list[str] = [f"{record['name']} — processeur Intel."]

#     if record.get("product_collection"):
#         parts.append(_sentence("Gamme", record["product_collection"]))

#     if record.get("vertical_segment"):
#         parts.append(_sentence("Segment d'usage", record["vertical_segment"]))

#     if record.get("status"):
#         parts.append(_sentence("Statut", record["status"]))

#     cores_bits = []
#     if record.get("cores") is not None:
#         cores_bits.append(f"{record['cores']} cœurs")
#     if record.get("threads") is not None:
#         cores_bits.append(f"{record['threads']} threads")
#     if cores_bits:
#         parts.append(_sentence("Cœurs/Threads", ", ".join(cores_bits)))

#     freqs = []
#     if record.get("base_frequency_ghz") is not None:
#         freqs.append(f"base {record['base_frequency_ghz']} GHz")
#     if record.get("max_turbo_ghz") is not None:
#         freqs.append(f"turbo max {record['max_turbo_ghz']} GHz")
#     if freqs:
#         parts.append(_sentence("Fréquences", ", ".join(freqs)))

#     if record.get("cache"):
#         parts.append(_sentence("Cache", record["cache"]))

#     if record.get("tdp_watts") is not None:
#         parts.append(_sentence("TDP", f"{record['tdp_watts']} W"))

#     if record.get("lithography_nm") is not None:
#         parts.append(_sentence("Gravure", f"{record['lithography_nm']} nm"))

#     if record.get("launch_quarter"):
#         parts.append(_sentence("Lancement", record["launch_quarter"]))

#     if record.get("recommended_price_usd") is not None:
#         parts.append(f"Prix conseillé Intel : {record['recommended_price_usd']} $.")

#     parts.append(_store_sentence(record["store_price_eur"], record["store_stock"]))

#     return " ".join(parts)


# def build_cpu_metadata(record: dict) -> dict[str, Any]:
#     metadata: dict[str, Any] = {
#         "id": record["id"],
#         "category": "cpu",
#         "name": record["name"],
#         "manufacturer": "Intel",
#         "store_price_eur": float(record["store_price_eur"]),
#         "store_stock": int(record["store_stock"]),
#         "in_stock": record["store_stock"] > 0,
#     }
#     if record.get("vertical_segment"):
#         metadata["vertical_segment"] = record["vertical_segment"]
#     if record.get("status"):
#         metadata["status"] = record["status"]
#     if record.get("cores") is not None:
#         metadata["cores"] = int(record["cores"])
#     if record.get("threads") is not None:
#         metadata["threads"] = int(record["threads"])
#     if record.get("tdp_watts") is not None:
#         metadata["tdp_watts"] = float(record["tdp_watts"])
#     if record.get("launch_quarter"):
#         metadata["launch_quarter"] = record["launch_quarter"]
#     return metadata


# # ─────────────────────────────────────────────────────────────────────
# # Orchestration
# # ─────────────────────────────────────────────────────────────────────
# def _load_json(path: Path) -> list[dict]:
#     if not path.exists():
#         raise FileNotFoundError(
#             f"{path} introuvable. As-tu lancé `python scripts/clean_data.py` "
#             "avant de construire les chunks ?"
#         )
#     with path.open("r", encoding="utf-8") as f:
#         return json.load(f)


# MAX_EXPECTED_CHUNK_CHARS = 2000


# def _to_chunk(chunk_id: str, text: str, metadata: dict) -> Chunk:
#     if len(text) > MAX_EXPECTED_CHUNK_CHARS:
#         logger.warning(
#             "Chunk %s anormalement long (%d caractères) — à vérifier.",
#             chunk_id,
#             len(text),
#         )
#     return Chunk(id=chunk_id, text=text, metadata=metadata)


# def build_gpu_chunks(records: list[dict]) -> list[Chunk]:
#     chunks = [
#         _to_chunk(r["id"], build_gpu_text(r), build_gpu_metadata(r)) for r in records
#     ]
#     logger.info("Chunking GPU : %d fiches -> %d chunks", len(records), len(chunks))
#     return chunks


# def build_cpu_chunks(records: list[dict]) -> list[Chunk]:
#     chunks = [
#         _to_chunk(r["id"], build_cpu_text(r), build_cpu_metadata(r)) for r in records
#     ]
#     logger.info("Chunking CPU : %d fiches -> %d chunks", len(records), len(chunks))
#     return chunks


# def build_all_chunks() -> list[Chunk]:
#     gpu_records = _load_json(GPU_JSON)
#     cpu_records = _load_json(CPU_JSON)

#     chunks = build_gpu_chunks(gpu_records) + build_cpu_chunks(cpu_records)
#     logger.info("Total : %d chunks prêts pour l'embedding", len(chunks))
#     return chunks


# # ─────────────────────────────────────────────────────────────────────
# # Test manuel rapide (voir section "comment tester" de l'explication)
# # ─────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     logging.basicConfig(
#         level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
#     )
#     all_chunks = build_all_chunks()

#     print("\n--- Exemple de chunk GPU (avec specs) ---")
#     example_gpu = next(
#         c
#         for c in all_chunks
#         if c.metadata["category"] == "gpu" and c.metadata["specs_available"]
#     )
#     print("ID:", example_gpu.id)
#     print("TEXTE:", example_gpu.text)
#     print("METADATA:", example_gpu.metadata)

#     print("\n--- Exemple de chunk GPU (prix récent seul) ---")
#     example_modern = next(
#         c
#         for c in all_chunks
#         if c.metadata["category"] == "gpu" and not c.metadata["specs_available"]
#     )
#     print("ID:", example_modern.id)
#     print("TEXTE:", example_modern.text)
#     print("METADATA:", example_modern.metadata)

#     print("\n--- Exemple de chunk CPU ---")
#     example_cpu = next(c for c in all_chunks if c.metadata["category"] == "cpu")
#     print("ID:", example_cpu.id)
#     print("TEXTE:", example_cpu.text)
#     print("METADATA:", example_cpu.metadata)
