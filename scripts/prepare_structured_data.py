from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd


RAW_DIR = Path("data/raw")
STRUCTURED_DIR = Path("data/structured")



SOURCE_FILES = [
    ("All_GPUs.csv", "GPU", None),
    ("Intel_CPUs.csv", "CPU", "Intel"),
    ("AMD_CPUs.csv", "CPU", "AMD"),
]


BRAND_COLUMN_CANDIDATES = [
    "manufacturer",
    "brand",
    "vendor",
    "company",
]

NAME_COLUMN_CANDIDATES = [
    "product_name",
    "productname",
    "name",
    "model",
    "processor_number",
]


def normalize_column_name(name: str) -> str:
    """
    Convert a CSV column name into a consistent snake_case format.

    Examples:
        "Processor Number" -> "processor_number"
        "Product Name"    -> "product_name"
    """
    name = unicodedata.normalize("NFKD", str(name))
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    return name.strip("_")


def clean_string(value: Any) -> str | None:
    """
    Clean a single value if it is a string.

    Empty values and NaN/NA values become None.
    """
    if value is None:
        return None

    if pd.isna(value):
        return None

    text = str(value).strip()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)

    return text or None


def clean_value(value: Any) -> Any:
    """
    Convert pandas-specific missing/numeric values into
    JSON-compatible Python values.

    Important:
        NaN / NaT / pandas.NA -> None
    """
    if value is None:
        return None

    # pandas missing values
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    # numpy/pandas integer/float values
    if hasattr(value, "item"):
        try:
            value = value.item()
        except (ValueError, TypeError):
            pass

    # Python float NaN / infinity are not valid JSON values.
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    if isinstance(value, str):
        return clean_string(value)

    return value


def load_csv_clean(path: Path) -> pd.DataFrame:
    """
    Load a CSV and clean its columns and values.
    """
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        print(f"  [warning] UTF-8 failed for {path.name}, trying latin-1...")
        df = pd.read_csv(path, encoding="latin-1")

    # Normalize column names.
    df.columns = [normalize_column_name(column) for column in df.columns]

    # Clean every cell.
    for column in df.columns:
        df[column] = df[column].map(clean_value)

    # Remove completely empty rows.
    before_empty = len(df)
    df = df.dropna(how="all")
    removed_empty = before_empty - len(df)

    if removed_empty:
        print(f"  - removed {removed_empty} completely empty rows")

    # Remove exact duplicate rows.
    before_duplicates = len(df)
    df = df.drop_duplicates()
    removed_duplicates = before_duplicates - len(df)

    if removed_duplicates:
        print(f"  - removed {removed_duplicates} exact duplicate rows")

    return df


def first_present(
    row: dict[str, Any],
    candidates: list[str],
) -> str | None:
    """
    Return the first non-empty value found among candidate columns.
    """
    for key in candidates:
        value = row.get(key)

        if value is None:
            continue

        if isinstance(value, str):
            value = value.strip()
            if not value:
                continue

        return str(value)

    return None


def make_json_safe(value: Any) -> Any:
    """
    Recursively convert values into strict JSON-compatible values.

    This prevents NaN/Infinity from appearing in products.json.
    """
    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if hasattr(value, "item"):
        try:
            return make_json_safe(value.item())
        except (ValueError, TypeError):
            pass

    return value


def build_products() -> tuple[
    list[dict[str, Any]],
    dict[str, set[str]],
]:
    """
    Build the structured product dataset from the configured CSV files.
    """
    products: list[dict[str, Any]] = []
    attributes_by_category: dict[str, set[str]] = {}

    next_id = 1

    for filename, category, brand_fallback in SOURCE_FILES:
        path = RAW_DIR / filename

        if not path.exists():
            print(
                f"[skip] {filename} not found in data/raw/ "
                f"— skipping."
            )
            continue

        print(f"\n[load] {filename}")

        df = load_csv_clean(path)

        print(f"  - rows available: {len(df)}")

        attributes_by_category.setdefault(category, set()).update(
            df.columns
        )

        dropped_missing_name = 0

        for record in df.to_dict(orient="records"):
            # Make sure every value is JSON-safe.
            record = make_json_safe(record)

            name = first_present(
                record,
                NAME_COLUMN_CANDIDATES,
            )

            if not name:
                dropped_missing_name += 1
                continue

            brand = (
                first_present(
                    record,
                    BRAND_COLUMN_CANDIDATES,
                )
                or brand_fallback
            )

            product = {
                "id": f"{category.lower()}_{next_id:05d}",
                "name": name,
                "category": category,
                "brand": brand,
                "specs": record,
            }

            products.append(product)
            next_id += 1

        if dropped_missing_name:
            print(
                f"  - dropped {dropped_missing_name} rows "
                f"with no product name"
            )

        print(
            f"  - products generated from {filename}: "
            f"{len(df) - dropped_missing_name}"
        )

    return products, attributes_by_category


def validate_products(products: list[dict[str, Any]]) -> None:
    """
    Validate basic data quality before writing the JSON files.
    """
    ids = [product["id"] for product in products]

    duplicate_ids = len(ids) - len(set(ids))

    if duplicate_ids:
        raise ValueError(
            f"Found {duplicate_ids} duplicate product IDs."
        )

    missing_names = [
        product["id"]
        for product in products
        if not product.get("name")
    ]

    if missing_names:
        raise ValueError(
            f"Products with missing names: {missing_names[:10]}"
        )

    print("\n[validation] Product validation passed.")
    print(f"[validation] Unique IDs: {len(set(ids))}")


def write_json(path: Path, data: Any) -> None:
    """
    Write strict UTF-8 JSON.
    allow_nan=False guarantees that NaN/Infinity
    cannot accidentally be written.
    """
    safe_data = make_json_safe(data)

    path.write_text(
        json.dumps(
            safe_data,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        ),
        encoding="utf-8",
    )


def main() -> None:
    STRUCTURED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("======================================")
    print(" TechCart - Structured Data Preparation")
    print("======================================")

    products, attributes_by_category = build_products()

    if not products:
        print(
            "\n[error] No products were generated."
        )
        print(
            "Make sure the raw CSV files exist in:"
        )
        print(
            f"  {RAW_DIR}"
        )
        return

    # Validate products before writing.
    validate_products(products)

    categories = sorted(
        {
            product["category"]
            for product in products
            if product.get("category")
        }
    )

    brands = sorted(
        {
            product["brand"]
            for product in products
            if product.get("brand")
        }
    )

    attributes = {
        category: sorted(columns)
        for category, columns in attributes_by_category.items()
    }

    # Write structured datasets.
    write_json(
        STRUCTURED_DIR / "products.json",
        products,
    )

    write_json(
        STRUCTURED_DIR / "categories.json",
        categories,
    )

    write_json(
        STRUCTURED_DIR / "brands.json",
        brands,
    )

    write_json(
        STRUCTURED_DIR / "attributes.json",
        attributes,
    )

    print("\n======================================")
    print(" Summary")
    print("======================================")

    print(f"Products:   {len(products)}")
    print(f"Categories: {categories}")
    print(f"Brands:     {brands}")

    print("\nWritten files:")

    print(
        f"  ✓ {STRUCTURED_DIR / 'products.json'}"
    )
    print(
        f"  ✓ {STRUCTURED_DIR / 'categories.json'}"
    )
    print(
        f"  ✓ {STRUCTURED_DIR / 'brands.json'}"
    )
    print(
        f"  ✓ {STRUCTURED_DIR / 'attributes.json'}"
    )

    print("\n[done] Structured data preparation completed.")


if __name__ == "__main__":
    main()