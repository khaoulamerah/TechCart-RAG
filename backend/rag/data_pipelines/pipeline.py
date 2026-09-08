from typing import Any

from backend.rag.data_pipelines.stages.base import Stage

from .utils import DataType


class Pipeline:
    datatype: DataType

    def __init__(
        self,
        stages: list[Stage],
    ) -> None:

        self.stages: list[Stage] = stages


    def set_datatype(self, datatype: DataType) -> None:
        self.datatype = datatype

    def run(
        self,
        data: list[str],
    ) -> Any:
        
        for stage in self.stages:
            stage.set_strategy(self.datatype)
            data = stage.run(data)

        return data