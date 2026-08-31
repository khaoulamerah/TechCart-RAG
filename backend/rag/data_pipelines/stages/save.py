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
