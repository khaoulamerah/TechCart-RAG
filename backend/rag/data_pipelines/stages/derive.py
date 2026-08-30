from __future__ import annotations

import logging

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Stage

logger = logging.getLogger("techcart.pipeline.derive")


class DeriveCategoriesBrandsAttributesStage(Stage[DataPipelineContext]):
    def run(self, data: DataPipelineContext) -> DataPipelineContext:
        data.categories = sorted({r["category"] for r in data.records if r.get("category")})
        data.brands = sorted({r["brand"] for r in data.records if r.get("brand")})

        attributes: dict[str, set[str]] = {}
        for record in data.records:
            category = record["category"]
            keys = set(record.get("specs", {}).keys())
            attributes.setdefault(category, set()).update(keys)

        data.attributes = {cat: sorted(keys) for cat, keys in attributes.items()}

        logger.info(
            "[derive] %d categories, %d brands, attributes for %d categories",
            len(data.categories), len(data.brands), len(data.attributes),
        )
        return data