from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)

from backend.rag.data_pipelines.strategies.derive.base import (
    DeriveStrategy,
)


class DeriveStage(Stage):

    def __init__(
        self,
        strategy: DeriveStrategy,
    ) -> None:

        self.strategy = strategy

    def run(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("DERIVE STAGE")
        print("=" * 60)

        derived_data = self.strategy.derive(data)

        return derived_data