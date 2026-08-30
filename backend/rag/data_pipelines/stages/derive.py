from backend.rag.data_pipelines.stages.base import Stage


class DeriveStage(Stage):

    def run(self, data):
        print("Deriving data...")

        return data