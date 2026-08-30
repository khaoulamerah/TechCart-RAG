from __future__ import annotations

import json
import logging
from pathlib import Path

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Stage

logger = logging.getLogger("techcart.pipeline.write")

STRUCTURED_DIR = Path("data/structured")


def _write_json(payload, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    logger.info("[write] %s", path)


class WriteStructuredJsonStage(Stage[DataPipelineContext]):
    def run(self, data: DataPipelineContext) -> DataPipelineContext:
        outputs = {
            STRUCTURED_DIR / "products.json": data.records,
            STRUCTURED_DIR / "categories.json": data.categories,
            STRUCTURED_DIR / "brands.json": data.brands,
            STRUCTURED_DIR / "attributes.json": data.attributes,
        }

        for path, payload in outputs.items():
            _write_json(payload, path)
            data.written_files.append(path)

        return data