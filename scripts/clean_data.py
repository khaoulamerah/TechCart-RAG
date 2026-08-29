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


def to_snake_case(value: str) -> str:
    """Convert a column name to snake_case."""

    value = str(value).strip()

    value = re.sub(r"[^\w\s]", "", value)
    value = re.sub(r"\s+", "_", value)
    value = re.sub(
        r"(?<!^)(?=[A-Z])",
        "_",
        value,
    )

    return value.lower().strip("_")


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize dataframe columns and values."""

    df = df.copy()

    df.columns = [
        to_snake_case(column)
        for column in df.columns
    ]

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
                    "None": pd.NA,
                    "NaN": pd.NA,
                }
            )

    df = df.dropna(how="all")

    df = df.drop_duplicates()

    return df


def detect_gpu_brand(
    manufacturer: Any,
) -> str | None:

    if manufacturer is None:
        return None

    value = str(manufacturer).strip().lower()

    if value == "nvidia":
        return "Nvidia"

    if value == "amd":
        return "AMD"

    if value == "ati":
        return "ATI"

    if value == "intel":
        return "Intel"

    return str(manufacturer).strip()


def detect_cpu_brand(
    row: pd.Series,
    filename: str,
) -> str:

    if filename == "amd_cpus.csv":
        return "AMD"

    return "Intel"


def clean_value(value: Any) -> Any:

    if pd.isna(value):
        return None

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


def build_gpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = {
        key: clean_value(value)
        for key, value in row.to_dict().items()
    }

    name = data.get("name")

    if not name:
        raise ValueError(
            f"GPU row {index} has no name."
        )

    manufacturer = detect_gpu_brand(
        data.get("manufacturer")
    )

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
        "specs": {
            **specs,
            "name": name,
            "manufacturer": (
                data.get("manufacturer")
            ),
        },
    }


def build_intel_cpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = {
        key: clean_value(value)
        for key, value in row.to_dict().items()
    }

    name = data.get("processor_number")

    if not name:
        raise ValueError(
            f"Intel CPU row {index} has no processor_number."
        )

    return {
        "id": f"cpu_{index + 1:05d}",
        "name": name,
        "category": "CPU",
        "brand": "Intel",
        "specs": data,
    }


def build_amd_cpu_record(
    row: pd.Series,
    index: int,
) -> dict[str, Any]:

    data = {
        key: clean_value(value)
        for key, value in row.to_dict().items()
    }

    name = data.get("cpu")

    if not name:
        raise ValueError(
            f"AMD CPU row {index} has no CPU name."
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
            f"Required source file not found: {path}"
        )

    # These files are CSV text files, even though
    # older versions were incorrectly named .xls.
    df = pd.read_csv(
        path,
        encoding="utf-8",
        low_memory=False,
    )

    return clean_dataframe(df)


def process_file(
    filename: str,
    category: str,
) -> list[dict[str, Any]]:

    df = read_source_file(filename)

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
                f"  [skip] {filename} row {index}: {exc}"
            )

    print(
        f"  [ok] {filename}: "
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
            {
                "name": record.get("name"),
                "category": record.get("category"),
                "brand": record.get("brand"),
                "specs": record.get("specs"),
            },
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

    attributes: dict[str, set[str]] = {}

    for record in records:

        category = record["category"]

        attributes.setdefault(
            category,
            set(),
        )

        specs = record.get("specs", {})

        attributes[category].update(
            specs.keys()
        )

    return {
        category: sorted(keys)
        for category, keys in attributes.items()
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

    print(f"  [write] {path}")


def main() -> None:

    print()
    print("=" * 70)
    print("TECHCART DATA CLEANING")
    print("=" * 70)
    print()

    all_records: list[dict[str, Any]] = []

    for filename, category in SOURCE_FILES.items():

        records = process_file(
            filename,
            category,
        )

        all_records.extend(records)

    if not all_records:

        raise RuntimeError(
            "No records were produced."
        )

    print()
    print("Removing duplicate records...")

    all_records = remove_duplicate_records(
        all_records
    )

    print(
        f"Unique records: {len(all_records)}"
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