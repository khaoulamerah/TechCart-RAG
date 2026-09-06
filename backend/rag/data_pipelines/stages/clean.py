from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)

from backend.rag.data_pipelines.strategies.cleaning.base import (
    CleaningStrategy,
)


class CleanStage(Stage):

    def __init__(
        self,
        strategy: CleaningStrategy,
    ) -> None:

        self.strategy = strategy

    def run(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("\n" + "=" * 60)
        print("CLEAN STAGE")
        print("=" * 60)

        for item in data:

            source: str = item["source"]

            print(f"\nCleaning: {source}")

            if "data" in item:

                cleaned_data = self.strategy.clean(
                    item["data"]
                )

                item["data"] = cleaned_data

            elif "content" in item:

                cleaned_content = self.strategy.clean(
                    item["content"]
                )

                item["content"] = cleaned_content

            else:

                raise ValueError(
                    f"Unknown data structure: {source}"
                )

        return data