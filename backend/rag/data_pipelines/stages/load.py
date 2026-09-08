from backend.rag.data_pipelines.stages.base import (
    FilePaths,
    PipelineData,
    Stage,
)
from backend.rag.data_pipelines.strategies.loading.base import (
    LoadingStrategy,
)
from backend.rag.data_pipelines.strategies.loading.strategies import (
    CsvLoadingStrategy,
    MarkdownLoadingStrategy,
)
from backend.rag.data_pipelines.utils import DataType


class LoadStage(Stage):

    def __init__(self) -> None:
        self.strategy: LoadingStrategy
        self.strategys = {
            DataType.CSV: CsvLoadingStrategy(),
            DataType.MD: MarkdownLoadingStrategy(),
        }

    def run(
        self,
        data: FilePaths,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("LOAD STAGE")
        print("=" * 60)

        loaded_data = self.strategy.load(data)

        return loaded_data