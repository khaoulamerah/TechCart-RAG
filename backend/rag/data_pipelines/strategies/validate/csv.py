
import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    FilePaths,
    PipelineData,
)

from backend.rag.data_pipelines.strategies.loading.base import (
    LoadingStrategy,
)


class CsvLoadingStrategy(LoadingStrategy):

    def load(self, data: FilePaths) -> PipelineData:

        print("Loading CSV data...")

        loaded_data: PipelineData = []

        for file_path in data:

            print(f"Loading: {file_path}")

            df: pd.DataFrame = pd.read_csv(file_path)

            loaded_data.append(
                {
                    "source": file_path,
                    "data": df,
                }
            )

        return loaded_data