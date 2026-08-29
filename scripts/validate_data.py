"""
Task 4 — Data Validation.

Checks:
  - every JSON file in data/structured/ is valid JSON and UTF-8
  - every JSON file is non-empty
  - product records have a 'category' field (required for later use)
  - every Markdown file in data/semi_structured/ is valid UTF-8 and non-empty
  - no duplicate product entries (by their raw dict content)
  - naming convention: files use snake_case, .json or .md extensions

Run from the project root:
    python scripts/validate_data.py
Exits with a non-zero status if any check fails, so it can be used
in CI later.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STRUCTURED_DIR = Path("data/structured")
SEMI_STRUCTURED_DIR = Path("data/semi_structured")

NAMING_PATTERN = re.compile(r"^[a-z0-9_]+\.(json|md)$")

errors: list[str] = []
warnings: list[str] = []


def check_naming(path: Path) -> None:
    if not NAMING_PATTERN.match(path.name):
        warnings.append(f"Non-standard filename: {path}")


def validate_json_file(path: Path) -> None:
    check_naming(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"Not valid UTF-8: {path}")
        return

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path}: {exc}")
        return

    if not data:
        errors.append(f"Empty JSON file: {path}")
        return

    if path.name == "products.json":
        validate_products(data, path)


def validate_products(data: list[dict], path: Path) -> None:
    if not isinstance(data, list):
        errors.append(f"{path}: expected a list of product records.")
        return

    seen = set()
    missing_category = 0
    duplicates = 0

    for record in data:
        if "category" not in record or not record["category"]:
            missing_category += 1

        fingerprint = json.dumps(record, sort_keys=True)
        if fingerprint in seen:
            duplicates += 1
        seen.add(fingerprint)

    if missing_category:
        errors.append(f"{path}: {missing_category} record(s) missing 'category'.")
    if duplicates:
        errors.append(f"{path}: {duplicates} duplicate record(s) found.")


def validate_markdown_file(path: Path) -> None:
    check_naming(path)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"Not valid UTF-8: {path}")
        return

    if not text.strip():
        errors.append(f"Empty Markdown file: {path}")


def main() -> None:
    print("Validating data/structured/ ...")
    if not STRUCTURED_DIR.exists():
        errors.append(f"Missing directory: {STRUCTURED_DIR}")
    else:
        for path in sorted(STRUCTURED_DIR.glob("*.json")):
            validate_json_file(path)

    print("Validating data/semi_structured/ ...")
    if not SEMI_STRUCTURED_DIR.exists():
        errors.append(f"Missing directory: {SEMI_STRUCTURED_DIR}")
    else:
        for path in sorted(SEMI_STRUCTURED_DIR.rglob("*.md")):
            validate_markdown_file(path)

    print()
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"{len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()