from __future__ import annotations

import logging
import re

import pandas as pd

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Stage

logger = logging.getLogger("techcart.pipeline.clean")


def to_snake_case(column_name: str) -> str:
    name = column_name.strip()
    name = re.sub(r"[^\w\s]", "", name)
    name = re.sub(r"\s+", "_", name)
    # Split camelCase boundaries (lower/digit -> Upper), e.g. "BoostClock".
    name = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name)
    # Split acronym boundaries (Upper -> Upper+lower), e.g. "HDMIPort" -> "HDMI_Port".
    # Whole-uppercase runs like "VRAM" or "TDP" have no such boundary and
    # stay intact instead of being split letter by letter.
    name = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", name)
    name = re.sub(r"_+", "_", name)  # collapse doubled underscores
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

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None, "": None})

    df = df.dropna(how="all")
    df = df.drop_duplicates()
    return df


class CleanAndTagStage(Stage[DataPipelineContext]):

    def run(self, data: DataPipelineContext) -> DataPipelineContext:
        for filename, (df, config) in data.raw.items():
            df = clean_dataframe(df)
            name_col = next(
                (c for c in df.columns if c in ("name", "model", "product_name", "cpu")),
                df.columns[0],
            )

            category = config["category"]
            brand_prefix = category
            counter = 0

            for _, row in df.iterrows():
                counter += 1
                row_dict = row.where(pd.notnull(row), None).to_dict()
                name = row_dict.get(name_col, "Unknown product")
                brand = guess_brand(name, config["brands"])

                specs = {k: v for k, v in row_dict.items() if k != name_col}

                data.records.append(
                    {
                        "id": f"{brand_prefix}_{(brand or 'unknown').lower()}_{counter:05d}",
                        "name": name,
                        "category": category.upper(),
                        "brand": brand,
                        "specs": specs,
                    }
                )

            logger.info("[clean] %s -> %d tagged records", filename, counter)

        return data