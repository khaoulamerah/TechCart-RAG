from backend.rag.data_pipelines.stages.base import Stage


class ValidateStage(Stage):

    def run(self, data):
        print("Validating data...")

        return data