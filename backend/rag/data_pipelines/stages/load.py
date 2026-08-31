import pandas as pd

from backend.rag.data_pipelines.stages.base import Stage


class LoadStage(Stage):

    def run(self, data):

        print("Loading data...")

        loaded_data = []

        for file_path in data:

            print(f"Loading: {file_path}")

            df = pd.read_csv(file_path)

            loaded_data.append({
                "source": file_path,
                "data": df,
            })

        return loaded_data