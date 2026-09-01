from pathlib import Path

from backend.rag.data_pipelines.stages.base import Stage


class SaveStage(Stage):
    def __init__(self, output_dir="data/processed"):
        self.output_dir = Path(output_dir)

    def run(self, data):

        print("Saving data...")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        for item in data:
            source = item["source"]
            df = item["data"]

            filename = Path(source).name

            output_path = self.output_dir / filename

            df.to_csv(output_path, index=False)

            print(f"Saved: {output_path}")

        return data
from pathlib import Path

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)


class SaveStage(Stage):

    def __init__(
        self,
        output_dir: str = "data/processed",
    ):
        self.output_dir: Path = Path(output_dir)

    def run(self, data: PipelineData) -> PipelineData:

        print("Saving CSV data...")

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for item in data:

            source: str = item["source"]
            df = item["data"]

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


class MarkdownSaveStage(Stage):

    def __init__(
        self,
        output_dir: str = "data/processed/markdown",
    ):
        self.output_dir: Path = Path(output_dir)

    def run(self, data: PipelineData) -> PipelineData:

        print("Saving Markdown data...")

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        for item in data:

            source: str = item["source"]
            content: str = item["content"]

            filename: str = Path(source).name

            output_path: Path = (
                self.output_dir / filename
            )

            output_path.write_text(
                content,
                encoding="utf-8",
            )

            print(f"Saved: {output_path}")

        return data