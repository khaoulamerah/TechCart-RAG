from __future__ import annotations

import logging

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Stage

logger = logging.getLogger("techcart.pipeline.validate")

REQUIRED_FIELDS = ("id", "name", "category")


class ValidateRecordsStage(Stage[DataPipelineContext]):
    def run(self, data: DataPipelineContext) -> DataPipelineContext:
        valid_records = []
        dropped = 0

        for record in data.records:
            missing = [f for f in REQUIRED_FIELDS if not record.get(f)]
            if missing:
                dropped += 1
                logger.warning(
                    "Dropping record missing %s: %s", missing, record.get("id", "?")
                )
                continue
            valid_records.append(record)

        if dropped:
            logger.warning("Validation dropped %d invalid record(s).", dropped)

        data.records = valid_records
        return data