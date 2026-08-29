
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
STRUCTURED_DIR = Path("data/structured")

# Map raw filename -> (category label, known brand keywords to detect)
SOURCE_FILES = {
    "All_GPUs.csv": {
        "category": "gpu",
        "brands": ["NVIDIA", "AMD", "Intel"],
    },
    "Intel_CPUs.csv": {
        "category": "cpu",
        "brands": ["Intel"],
    },
}


def to_snake_case(column_name: str) -> str:
    name = column_name.strip()
    name = re.sub(r"[^\w\s]", "", name)          # drop punctuation
    name = re.sub(r"\s+", "_", name)              # spaces -> underscores
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name)   # camelCase -> snake_case
    return name.lower().strip("_")


def guess_brand(name: str, known_brands: list[str]) -> str | None:
    if not isinstance(name, str):
        return None
    for brand in known_brands:
        if brand.lower() in name.lower():
            return brand
    return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [to_snake_case(c) for c in df.columns]

    # Strip whitespace on every text column.
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    df = df.dropna(how="all")
    df = df.drop_duplicates()
    return df


def process_file(filename: str, config: dict) -> list[dict]:
    path = RAW_DIR / filename
    if not path.exists():
        print(f"  [skip] {filename} not found in {RAW_DIR}/")
        return []

    df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    df = clean_dataframe(df)

    name_col = next(
        (c for c in df.columns if c in ("name", "model", "product_name")),
        df.columns[0],
    )

    records = []
    for _, row in df.iterrows():
        record = row.where(pd.notnull(row), None).to_dict()
        record["category"] = config["category"]
        record["brand"] = guess_brand(record.get(name_col, ""), config["brands"])
        records.append(record)

    print(f"  [ok]   {filename}: {len(records)} rows -> category='{config['category']}'")
    return records


def build_categories_and_brands(all_records: list[dict]) -> tuple[list[dict], list[dict]]:
    categories = sorted({r["category"] for r in all_records if r.get("category")})
    brands = sorted({r["brand"] for r in all_records if r.get("brand")})

    categories_json = [{"id": c, "name": c.upper()} for c in categories]
    brands_json = [{"id": b.lower().replace(" ", "_"), "name": b} for b in brands]
    return categories_json, brands_json


def write_json(data, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [write] {path} ({len(data)} entries)")


def main() -> None:
    print("Cleaning raw CSVs into data/structured/ ...")
    all_records: list[dict] = []

    for filename, config in SOURCE_FILES.items():
        all_records.extend(process_file(filename, config))

    if not all_records:
        print("No records produced — check that your CSVs are in data/raw/.")
        return

    categories, brands = build_categories_and_brands(all_records)

    write_json(all_records, STRUCTURED_DIR / "products.json")
    write_json(categories, STRUCTURED_DIR / "categories.json")
    write_json(brands, STRUCTURED_DIR / "brands.json")

    # attributes.json: the set of spec fields available per category,
    # useful later for building filters/UI without re-scanning products.json.
    attributes: dict[str, list[str]] = {}
    for record in all_records:
        cat = record["category"]
        keys = [k for k in record.keys() if k not in ("category", "brand")]
        attributes.setdefault(cat, set()).update(keys)
    attributes = {cat: sorted(keys) for cat, keys in attributes.items()}
    write_json(attributes, STRUCTURED_DIR / "attributes.json")

    print("Done.")


if __name__ == "__main__":
    main()