from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
STRUCTURED_DIR = PROJECT_ROOT / "data" / "structured"


SOURCE_FILES = {
    "All_GPUs.csv": "GPU",
    "Intel_CPUs.csv": "CPU",
    "amd_cpus.csv": "CPU",
}


def normalize_column_name(value: str) -> str:
    """
    Normalize a source column name to snake_case.

    Handles acronyms such as CPU, GPU, HDMI, DVI, etc.
    """

    value = str(value).strip()

    # Remove BOM if present.
    value = value.replace("\ufeff", "")

    # Normalize separators.
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)

    # Handle acronym -> word transitions.
    value = re.sub(
        r"([A-Z]+)([A-Z][a-z])",
        r"\1_\2",
        value,
    )

    # Handle lower/number -> upper transitions.
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1_\2",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return value.lower().strip("_")


def normalize_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize columns and remove empty/duplicate rows."""

    df = df.copy()

    df.columns = [
        normalize_column_name(column)
        for column in df.columns
    ]

    # Normalize string values.
    for column in df.columns:

        if df[column].dtype == "object":

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

            df[column] = df[column].replace(
                {
                    "": pd.NA,
                    "nan": pd.NA,
                    "NaN": pd.NA,
                    "None": pd.NA,
                    "null": pd.NA,
                }
            )

    # Remove completely empty rows.
    df = df.dropna(how="all")

    # Remove exact duplicate rows.
    df = df.drop_duplicates()

    return df


def clean_value(value: Any) -> Any:
    """Convert pandas values into JSON-safe values."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return None

        return value

    if hasattr(value, "item"):

        try:
            return value.item()
        except (ValueError, TypeError):
            pass

    return value


def row_to_dict(
    row: pd.Series,
) -> dict[str, Any]:
    return {
        key: clean_value(value)
        for key, value in row.to_dict().items()
    }


def detect_gpu_brand(
    manufacturer: Any,
) -> str | None:

    if manufacturer is None:
        return None

    value = str(manufacturer).strip().lower()

    mapping = {
        "nvidia": "Nvidia",
        "amd": "AMD",
        "ati": "ATI",
        "intel": "Intel",
    }

    return mapping.get(
        value,
        str(manufacturer).strip(),
    )


def build_gpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = row_to_dict(row)

    name = data.get("name")

    if not name:
        raise ValueError(
            "GPU has no name."
        )

    manufacturer = detect_gpu_brand(
        data.get("manufacturer")
    )

    # Keep source fields under specs.
    specs = {
        key: value
        for key, value in data.items()
        if key != "name"
    }

    return {
        "id": f"gpu_{index + 1:05d}",
        "name": name,
        "category": "GPU",
        "brand": manufacturer,
        "specs": specs,
    }


def build_intel_cpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = row_to_dict(row)

    name = data.get(
        "processor_number"
    )

    if not name:
        raise ValueError(
            "Intel CPU has no processor_number."
        )

    return {
        "id": f"cpu_intel_{index + 1:05d}",
        "name": name,
        "category": "CPU",
        "brand": "Intel",
        "specs": data,
    }


def build_amd_cpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = row_to_dict(row)

    name = data.get("cpu")

    if not name:
        raise ValueError(
            "AMD CPU has no CPU name."
        )

    return {
        "id": f"cpu_amd_{index + 1:05d}",
        "name": name,
        "category": "CPU",
        "brand": "AMD",
        "specs": data,
    }


def read_source_file(
    filename: str,
) -> pd.DataFrame:

    path = RAW_DIR / filename

    if not path.exists():

        raise FileNotFoundError(
            f"Source file not found: {path}"
        )

    df = pd.read_csv(
        path,
        encoding="utf-8",
        low_memory=False,
    )

    return normalize_dataframe(df)


def process_file(
    filename: str,
    category: str,
) -> list[dict[str, Any]]:

    df = read_source_file(filename)

    print(
        f"\nProcessing {filename}"
    )

    print(
        f"Rows found: {len(df)}"
    )

    print(
        "Columns:",
        ", ".join(df.columns),
    )

    records: list[dict[str, Any]] = []

    for index, row in df.iterrows():

        try:

            if filename == "All_GPUs.csv":

                record = build_gpu_record(
                    row,
                    index,
                )

            elif filename == "Intel_CPUs.csv":

                record = build_intel_cpu_record(
                    row,
                    index,
                )

            elif filename == "amd_cpus.csv":

                record = build_amd_cpu_record(
                    row,
                    index,
                )

            else:

                raise ValueError(
                    f"Unsupported source file: {filename}"
                )

            records.append(record)

        except ValueError as exc:

            print(
                f"[skip] {filename} "
                f"row {index}: {exc}"
            )

    print(
        f"[ok] {filename}: "
        f"{len(records)} records"
    )

    return records


def remove_duplicate_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    unique: list[dict[str, Any]] = []

    seen: set[str] = set()

    for record in records:

        fingerprint = json.dumps(
            record,
            sort_keys=True,
            ensure_ascii=False,
        )

        if fingerprint in seen:
            continue

        seen.add(fingerprint)

        unique.append(record)

    return unique


def build_categories(
    records: list[dict[str, Any]],
) -> list[str]:

    return sorted(
        {
            record["category"]
            for record in records
            if record.get("category")
        }
    )


def build_brands(
    records: list[dict[str, Any]],
) -> list[str]:

    return sorted(
        {
            record["brand"]
            for record in records
            if record.get("brand")
        }
    )


def build_attributes(
    records: list[dict[str, Any]],
) -> dict[str, list[str]]:

    result: dict[str, set[str]] = {}

    for record in records:

        category = record["category"]

        result.setdefault(
            category,
            set(),
        )

        specs = record.get(
            "specs",
            {},
        )

        result[category].update(
            specs.keys()
        )

    return {
        category: sorted(attributes)
        for category, attributes in result.items()
    }


def write_json(
    data: Any,
    path: Path,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"[write] {path}"
    )


def main() -> None:

    print()
    print("=" * 70)
    print("TECHCART DATA CLEANING")
    print("=" * 70)

    all_records: list[dict[str, Any]] = []

    for filename, category in SOURCE_FILES.items():

        records = process_file(
            filename,
            category,
        )

        all_records.extend(records)

    if not all_records:

        raise RuntimeError(
            "No records were generated."
        )

    print()
    print("Removing duplicate records...")

    before = len(all_records)

    all_records = remove_duplicate_records(
        all_records
    )

    print(
        f"Duplicates removed: "
        f"{before - len(all_records)}"
    )

    print(
        f"Final records: "
        f"{len(all_records)}"
    )

    categories = build_categories(
        all_records
    )

    brands = build_brands(
        all_records
    )

    attributes = build_attributes(
        all_records
    )

    write_json(
        all_records,
        STRUCTURED_DIR / "products.json",
    )

    write_json(
        categories,
        STRUCTURED_DIR / "categories.json",
    )

    write_json(
        brands,
        STRUCTURED_DIR / "brands.json",
    )

    write_json(
        attributes,
        STRUCTURED_DIR / "attributes.json",
    )

    print()
    print("=" * 70)
    print("DATA CLEANING COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()