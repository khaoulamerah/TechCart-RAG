from pathlib import Path

import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    FilePaths,
    PipelineData,
    Stage,
)


class LoadStage(Stage):

    def run(self, data: FilePaths) -> PipelineData:

        print("Loading data...")

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


class MarkdownLoadStage(Stage):

    def run(self, data: FilePaths) -> PipelineData:

        print("Loading Markdown documents...")

        loaded_documents: PipelineData = []

        for file_path in data:

            print(f"Loading: {file_path}")

            path: Path = Path(file_path)

            content: str = path.read_text(
                encoding="utf-8"
            )

            loaded_documents.append(
                {
                    "source": file_path,
                    "content": content,
                }
            )

        return loaded_documents