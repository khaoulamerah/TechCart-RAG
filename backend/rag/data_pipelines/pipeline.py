from typing import Any

from backend.rag.data_pipelines.stages.base import Stage


class Pipeline:

    def __init__(
        self,
        stages: list[Stage],
    ) -> None:

        self.stages: list[Stage] = stages

    def run(
        self,
        data: Any,
    ) -> Any:

        for stage in self.stages:
            data = stage.run(data)

        return data