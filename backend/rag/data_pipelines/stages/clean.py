
from backend.rag.data_pipelines.stages import Stage

class CleanStage(Stage):
    def run(self,data):
        print("Cleaning data...")
        return data