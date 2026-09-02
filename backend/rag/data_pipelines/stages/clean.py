from backend.rag.data_pipelines.stages.base import Stage
from backend.rag.data_pipelines.strategies.cleaning.base import (
    CleaningStrategy,
)


class CleanStage(Stage):

    def __init__(
        self,
        strategy: CleaningStrategy,
    ) -> None:

        self.strategy = strategy

    def run(self, data):

        print("\n" + "=" * 60)
        print("CLEAN STAGE")
        print("=" * 60)

        for item in data:

            source = item["source"]

            print(f"\nCleaning: {source}")

            cleaned_data = self.strategy.clean(
                item["data"]
            )

            item["data"] = cleaned_data

        return data