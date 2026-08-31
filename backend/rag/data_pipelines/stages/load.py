import pandas as pd

from backend.rag.data_pipelines.stages.base import Stage


class LoadStage(Stage):

    def run(self, data):
        print(f"Loading data from: {data}")

        df = pd.read_csv(data)

        print(f"Loaded {len(df)} rows")
        print(f"Columns: {len(df.columns)}")

        return df