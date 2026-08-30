from backend.rag.data_pipelines.stages.base import Stage


class SaveStage(Stage):

    def run(self, data):
        print("Saving data...")

        return data