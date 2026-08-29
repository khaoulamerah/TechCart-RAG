from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STRUCTURED_DIR = PROJECT_ROOT / "data" / "structured"
SEMI_STRUCTURED_DIR = (
    PROJECT_ROOT / "data" / "semi_structured"
)

NAMING_PATTERN = re.compile(
    r"^[a-z0-9_]+\.(json|md)$"
)

errors: list[str] = []
warnings: list[str] = []


def check_naming(path: Path) -> None:

    if not NAMING_PATTERN.match(path.name):

        warnings.append(
            f"Non-standard filename: {path}"
        )


def validate_json_file(path: Path) -> None:

    check_naming(path)

    try:

        text = path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        errors.append(
            f"Not valid UTF-8: {path}"
        )

        return

    try:

        data = json.loads(text)

    except json.JSONDecodeError as exc:

        errors.append(
            f"Invalid JSON in {path}: {exc}"
        )

        return

    if not data:

        errors.append(
            f"Empty JSON file: {path}"
        )

        return

    if path.name == "products.json":

        validate_products(
            data,
            path,
        )


def validate_products(
    data: Any,
    path: Path,
) -> None:

    if not isinstance(data, list):

        errors.append(
            f"{path}: expected a list."
        )

        return

    seen: set[str] = set()

    for index, record in enumerate(data):

        if not isinstance(record, dict):

            errors.append(
                f"{path}: record {index} "
                f"is not an object."
            )

            continue

        required_fields = {
            "id",
            "name",
            "category",
            "brand",
            "specs",
        }

        missing = (
            required_fields
            - record.keys()
        )

        if missing:

            errors.append(
                f"{path}: record {index} "
                f"missing fields: "
                f"{', '.join(sorted(missing))}"
            )

        if not record.get("name"):

            errors.append(
                f"{path}: record {index} "
                "has an empty name."
            )

        if not record.get("category"):

            errors.append(
                f"{path}: record {index} "
                "has an empty category."
            )

        if not isinstance(
            record.get("specs"),
            dict,
        ):

            errors.append(
                f"{path}: record {index} "
                "'specs' must be an object."
            )

        fingerprint = json.dumps(
            record,
            sort_keys=True,
            ensure_ascii=False,
        )

        if fingerprint in seen:

            errors.append(
                f"{path}: duplicate record "
                f"at index {index}."
            )

        seen.add(fingerprint)


def validate_markdown_file(
    path: Path,
) -> None:

    check_naming(path)

    try:

        text = path.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:

        errors.append(
            f"Not valid UTF-8: {path}"
        )

        return

    if not text.strip():

        errors.append(
            f"Empty Markdown file: {path}"
        )


def main() -> None:

    print()
    print("Validating structured data...")

    if not STRUCTURED_DIR.exists():

        errors.append(
            f"Missing directory: "
            f"{STRUCTURED_DIR}"
        )

    else:

        for path in sorted(
            STRUCTURED_DIR.glob("*.json")
        ):

            validate_json_file(path)

    print("Validating semi-structured data...")

    if not SEMI_STRUCTURED_DIR.exists():

        errors.append(
            f"Missing directory: "
            f"{SEMI_STRUCTURED_DIR}"
        )

    else:

        for path in sorted(
            SEMI_STRUCTURED_DIR.rglob("*.md")
        ):

            validate_markdown_file(path)

    print()

    if warnings:

        print(
            f"{len(warnings)} warning(s):"
        )

        for warning in warnings:

            print(
                f"  - {warning}"
            )

        print()

    if errors:

        print(
            f"{len(errors)} error(s):"
        )

        for error in errors:

            print(
                f"  - {error}"
            )

        sys.exit(1)

    print("All checks passed.")


if __name__ == "__main__":
    main()