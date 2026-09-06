from pathlib import Path

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)

from backend.rag.data_pipelines.strategies.save.base import (
    SaveStrategy,
)


class MarkdownSaveStrategy(SaveStrategy):

    def __init__(
        self,
        output_dir: str = "data/processed/markdown",
    ) -> None:

        self.output_dir: Path = Path(output_dir)

    def save(
        self,
        data: PipelineData,
    ) -> PipelineData:

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