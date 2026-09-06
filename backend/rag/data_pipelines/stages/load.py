from backend.rag.data_pipelines.stages.base import (
    FilePaths,
    PipelineData,
    Stage,
)

from backend.rag.data_pipelines.strategies.loading.base import (
    LoadingStrategy,
)


class LoadStage(Stage):

    def __init__(
        self,
        strategy: LoadingStrategy,
    ) -> None:

        self.strategy = strategy

    def run(
        self,
        data: FilePaths,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("LOAD STAGE")
        print("=" * 60)

        loaded_data = self.strategy.load(data)

        return loaded_data