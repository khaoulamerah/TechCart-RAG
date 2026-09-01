import pandas as pd

from pathlib import Path

from backend.rag.data_pipelines.stages.base import Stage


class LoadStage(Stage):

    def run(self, data):

        print("Loading data...")

        loaded_data = []

        for file_path in data:

            print(f"Loading: {file_path}")

            df = pd.read_csv(file_path)

            loaded_data.append(
                {
                    "source": file_path,
                    "data": df,
                }
            )

        return loaded_data


class MarkdownLoadStage(Stage):

    def run(self, data):

        print("Loading Markdown documents...")

        loaded_documents = []

        for file_path in data:

            print(f"Loading: {file_path}")

            path = Path(file_path)

            content = path.read_text(encoding="utf-8")

            loaded_documents.append(
                {
                    "source": file_path,
                    "content": content,
                }
            )

        return loaded_documents