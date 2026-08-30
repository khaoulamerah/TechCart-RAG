from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Stage

logger = logging.getLogger("techcart.pipeline.load")

RAW_DIR = Path("data/raw")

# Same config as the previous clean_data.py — unchanged behavior,
# just relocated so it belongs to the stage that actually uses it.
SOURCE_FILES = {
    "All_GPUs.csv": {"category": "gpu", "brands": ["NVIDIA", "AMD", "Intel"]},
    "Intel_CPUs.csv": {"category": "cpu", "brands": ["Intel"]},
    "AMD_CPUs.csv": {"category": "cpu", "brands": ["AMD"]},
}


class LoadRawFilesStage(Stage[DataPipelineContext]):
    def run(self, data: DataPipelineContext) -> DataPipelineContext:
        for filename, config in SOURCE_FILES.items():
            path = RAW_DIR / filename
            if not path.exists():
                logger.warning("[skip] %s not found in %s/", filename, RAW_DIR)
                continue

            df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
            data.raw[filename] = (df, config)
            logger.info("[load] %s: %d raw rows", filename, len(df))

        return data