from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)
from backend.rag.data_pipelines.strategies.derive.base import (
    DeriveStrategy,
)
from backend.rag.data_pipelines.strategies.derive.strategies import (
    CsvDeriveStrategy,
    MarkdownDeriveStrategy,
)
from backend.rag.data_pipelines.utils import DataType


class DeriveStage(Stage):

    def __init__(self) -> None:
        self.strategy: DeriveStrategy
        self.strategys = {
            DataType.CSV: CsvDeriveStrategy(),
            DataType.MD: MarkdownDeriveStrategy(),
        }

    def run(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("DERIVE STAGE")
        print("=" * 60)

        derived_data = self.strategy.derive(data)

        return derived_data