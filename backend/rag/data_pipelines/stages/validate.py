from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)

from backend.rag.data_pipelines.strategies.validate.base import (
    ValidationStrategy,
)


class ValidateStage(Stage):

    def __init__(
        self,
        strategy: ValidationStrategy,
    ) -> None:

        self.strategy = strategy

    def run(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("VALIDATE STAGE")
        print("=" * 60)

        validated_data = self.strategy.validate(
            data
        )

        return validated_data