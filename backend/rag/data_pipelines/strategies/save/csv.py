from pathlib import Path

import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)

from backend.rag.data_pipelines.strategies.save.base import (
    SaveStrategy,
)


class CsvSaveStrategy(SaveStrategy):

    def __init__(
        self,
        output_dir: str = "data/processed",
    ) -> None:

        self.output_dir: Path = Path(output_dir)

    def save(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("Saving CSV data...")

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for item in data:

            source: str = item["source"]
            df: pd.DataFrame = item["data"]

            filename: str = Path(source).name

            output_path: Path = (
                self.output_dir / filename
            )

            df.to_csv(
                output_path,
                index=False,
            )

            print(f"Saved: {output_path}")

        return data