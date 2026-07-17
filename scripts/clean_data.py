
from __future__ import annotations

import json
import logging
import random
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

GPU_CSV = RAW_DIR / "All_GPUs.csv"
CPU_CSV = RAW_DIR / "Intel_CPUs.csv"
GPU_OUTPUT = PROCESSED_DIR / "gpus.json"
CPU_OUTPUT = PROCESSED_DIR / "cpus.json"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("techcart.clean_data")



def clean_str(value: Any) -> Optional[str]:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text in ("", "-", "N/A", "NA", "n/a"):
        return None
    return text


def extract_number(value: Any, as_int: bool = False) -> Optional[float]:
    text = clean_str(value)
    if text is None:
        return None
    match = re.search(r"[-+]?\d*\.?\d+", text)
    if not match:
        return None
    number = float(match.group())
    return int(number) if as_int else number


def parse_price_usd(value: Any) -> Optional[float]:
    text = clean_str(value)
    if text is None:
        return None
    match = re.search(r"[\d.]+", text.replace(",", ""))
    return float(match.group()) if match else None


def parse_release_date(value: Any) -> Optional[str]:
    text = clean_str(value)
    if text is None:
        return None
    try:
        return datetime.strptime(text, "%d-%b-%Y").date().isoformat()
    except ValueError:
        logger.debug("Date GPU non reconnue, ignorée: %r", text)
        return None


def parse_launch_quarter(value: Any) -> Optional[str]:
    text = clean_str(value)
    if text is None:
        return None
    match = re.match(r"Q(\d)'(\d{2})", text)
    if not match:
        # Format inattendu : on garde la valeur brute plutôt que de
        # silencieusement perdre l'information.
        return text
    quarter, year_suffix = match.groups()
    year = 2000 + int(year_suffix)
    return f"{year}-Q{quarter}"


def parse_yes_no(value: Any) -> Optional[bool]:
    """Convertit 'Yes'/'No' en booléen Python. None si absent."""
    text = clean_str(value)
    if text is None:
        return None
    return text.lower() == "yes"


def mb_string_to_gb(value: Any) -> Optional[float]:
    megabytes = extract_number(value)
    return round(megabytes / 1024, 3) if megabytes is not None else None


def _deterministic_seed(identifier: str) -> int:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def simulate_store_price_eur(
    seed_key: str,
    reference_price_usd: Optional[float],
    fallback_range: tuple[float, float] = (80.0, 700.0),
) -> float:
    rng = random.Random(_deterministic_seed(seed_key))
    if reference_price_usd:
        eur = reference_price_usd * 0.93
        eur *= rng.uniform(0.85, 1.15)
    else:
        eur = rng.uniform(*fallback_range)
    return round(max(eur, 15.0), 2)


def simulate_store_stock(seed_key: str) -> int:
    rng = random.Random(_deterministic_seed(seed_key + "::stock"))
    if rng.random() < 0.15:
        return 0
    return rng.randint(1, 40)



def clean_gpus() -> list[dict]:
    if not GPU_CSV.exists():
        raise FileNotFoundError(f"Fichier introuvable : {GPU_CSV}")

    df = pd.read_csv(GPU_CSV)
    logger.info("GPU : %d lignes brutes chargées depuis %s", len(df), GPU_CSV.name)

    records: list[dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        name = clean_str(row["Name"])
        if not name:
            skipped += 1
            continue

        manufacturer = clean_str(row["Manufacturer"]) or "Unknown"
        release_price = parse_price_usd(row["Release_Price"])
        seed_key = f"{manufacturer}|{name}"

        records.append({
            "id": f"gpu_{idx:05d}",
            "category": "gpu",
            "name": name,
            "manufacturer": manufacturer,
            "architecture": clean_str(row["Architecture"]),
            "is_notebook_gpu": parse_yes_no(row["Notebook_GPU"]),
            "core_clock_mhz": extract_number(row["Core_Speed"]),
            "boost_clock_mhz": extract_number(row["Boost_Clock"]),
            "memory_gb": mb_string_to_gb(row["Memory"]),
            "memory_type": clean_str(row["Memory_Type"]),
            "memory_bus_bit": extract_number(row["Memory_Bus"], as_int=True),
            "memory_bandwidth_gb_s": extract_number(row["Memory_Bandwidth"]),
            "process_nm": extract_number(row["Process"]),
            "max_power_watts": extract_number(row["Max_Power"]),
            "best_resolution": clean_str(row["Best_Resolution"]),
            "direct_x": clean_str(row["Direct_X"]),
            "open_gl": clean_str(row["Open_GL"]),
            "release_date": parse_release_date(row["Release_Date"]),
            # Donnée RÉELLE du dataset (peut être null) — ne jamais
            # confondre avec le champ simulé ci-dessous.
            "release_price_usd": release_price,
            # Donnée SIMULÉE pour les besoins de la démo e-commerce.
            "store_price_eur": simulate_store_price_eur(seed_key, release_price),
            "store_stock": simulate_store_stock(seed_key),
        })

    logger.info(
        "GPU : %d fiches nettoyées, %d lignes écartées (nom manquant)",
        len(records), skipped,
    )
    return records



def clean_cpus() -> list[dict]:
    if not CPU_CSV.exists():
        raise FileNotFoundError(f"Fichier introuvable : {CPU_CSV}")

    df = pd.read_csv(CPU_CSV)
    logger.info("CPU : %d lignes brutes chargées depuis %s", len(df), CPU_CSV.name)

    records: list[dict] = []
    skipped = 0

    for idx, row in df.iterrows():
        processor_number = clean_str(row["Processor_Number"])
        collection = clean_str(row["Product_Collection"])
        # Certaines lignes n'ont pas de Processor_Number (références
        # "legacy") : on retombe sur la collection comme nom lisible.
        name = f"Intel {processor_number}" if processor_number else collection
        if not name:
            skipped += 1
            continue

        recommended_price = parse_price_usd(row["Recommended_Customer_Price"])
        seed_key = f"{processor_number or collection}|{idx}"

        records.append({
            "id": f"cpu_{idx:05d}",
            "category": "cpu",
            "name": name,
            "processor_number": processor_number,
            "product_collection": collection,
            "vertical_segment": clean_str(row["Vertical_Segment"]),  # Desktop / Mobile / Server / Embedded
            "status": clean_str(row["Status"]),
            "cores": extract_number(row["nb_of_Cores"], as_int=True),
            "threads": extract_number(row["nb_of_Threads"], as_int=True),
            "base_frequency_ghz": extract_number(row["Processor_Base_Frequency"]),
            "max_turbo_ghz": extract_number(row["Max_Turbo_Frequency"]),
            "cache": clean_str(row["Cache"]),
            "tdp_watts": extract_number(row["TDP"]),
            "lithography_nm": extract_number(row["Lithography"]),
            "launch_quarter": parse_launch_quarter(row["Launch_Date"]),
            "recommended_price_usd": recommended_price,
            "store_price_eur": simulate_store_price_eur(seed_key, recommended_price),
            "store_stock": simulate_store_stock(seed_key),
        })

    logger.info(
        "CPU : %d fiches nettoyées, %d lignes écartées (nom manquant)",
        len(records), skipped,
    )
    return records


def write_json(records: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Écrit %d enregistrements -> %s", len(records), output_path)


def main() -> None:
    logger.info("=== TechCart · Étape 1 : Nettoyage des données ===")

    gpus = clean_gpus()
    write_json(gpus, GPU_OUTPUT)

    cpus = clean_cpus()
    write_json(cpus, CPU_OUTPUT)

    logger.info("--- Résumé ---")
    logger.info("GPU  : %d fiches -> %s", len(gpus), GPU_OUTPUT)
    logger.info("CPU  : %d fiches -> %s", len(cpus), CPU_OUTPUT)
    logger.info("=== Terminé ===")


if __name__ == "__main__":
    main()