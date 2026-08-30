from backend.rag.data_pipelines.pipeline import Pipeline


from backend.rag.data_pipelines.stages.load import LoadStage
from backend.rag.data_pipelines.stages.validate import ValidateStage
from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.save import SaveStage

def main():
    pipeline=pipeline(
        stages=[
            LoadStage(),
            CleanStage(),
            ValidateStage(),
            DeriveStage(),
            SaveStage(),
        ]
    )

    data="products.csv"
    results = pipeline.run(data)

    print("Pipeline finished")
    print(result)



if __name__ == "__main__":
    main()
    
