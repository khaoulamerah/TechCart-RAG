from pathlib import Path

from backend.rag.data_pipelines.stages.base import (
    FilePaths,
    PipelineData,
)

from backend.rag.data_pipelines.strategies.loading.base import (
    LoadingStrategy,
)


class MarkdownLoadingStrategy(LoadingStrategy):

    def load(self, data: FilePaths) -> PipelineData:

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