
from backend.rag.data_pipelines.stages import Stage

class LoadStage(Stage):

    def run(self,data):
        print("Loading data...")
        return data
