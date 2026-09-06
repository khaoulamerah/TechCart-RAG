from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)

from backend.rag.data_pipelines.strategies.save.base import (
    SaveStrategy,
)


class SaveStage(Stage):

    def __init__(
        self,
        strategy: SaveStrategy,
    ) -> None:

        self.strategy = strategy

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