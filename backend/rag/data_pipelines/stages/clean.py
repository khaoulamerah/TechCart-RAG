from backend.rag.data_pipelines.stages.base import Stage


class CleanStage(Stage):

    def run(self, data):
        print("Cleaning data...")

        return data