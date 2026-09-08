from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)
from backend.rag.data_pipelines.strategies.validate.base import (
    ValidationStrategy,
)
from backend.rag.data_pipelines.strategies.validate.strategies import (
    CsvValidationStrategy,
    MarkdownValidationStrategy,
)
from backend.rag.data_pipelines.utils import DataType


class ValidateStage(Stage):

    def __init__(self) -> None:
        self.strategy: ValidationStrategy
        self.strategys = {
            DataType.CSV: CsvValidationStrategy(),
            DataType.MD: MarkdownValidationStrategy(),
        }

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