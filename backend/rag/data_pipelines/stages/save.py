from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)
from backend.rag.data_pipelines.strategies.save.base import (
    SaveStrategy,
)
from backend.rag.data_pipelines.strategies.save.strategies import (
    CsvSaveStrategy,
    MarkdownSaveStrategy,
)
from backend.rag.data_pipelines.utils import DataType


class SaveStage(Stage):

    def __init__(self) -> None:
        self.strategy: SaveStrategy
        self.strategys = {
            DataType.CSV: CsvSaveStrategy(),
            DataType.MD: MarkdownSaveStrategy(),
        }

    def run(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("SAVE STAGE")
        print("=" * 60)

        saved_data = self.strategy.save(
            data
        )

        return saved_data