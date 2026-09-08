from typing import Any

from backend.rag.data_pipelines.utils import DataType

FilePaths = list[str]

PipelineData = list[dict[str, Any]]


class Stage:

    def __init__(self) -> None:
        self.strategy: Any
        self.strategys: dict[DataType, Any] = {} #regestry like 
    
    def run(self, data: Any) -> Any:
        ...

    def set_strategy(self, datatype: DataType) -> None:
        try:
            self.strategy = self.strategys[datatype]
        except KeyError:
            raise ValueError(
                f"Unknown Strategy: {datatype}"
            )
