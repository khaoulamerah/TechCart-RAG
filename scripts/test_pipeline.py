from backend.rag.data_pipelines.pipeline import Pipeline

from backend.rag.data_pipelines.stages.load import LoadStage
from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.validate import ValidateStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.save import SaveStage


def create_pipeline():

    return Pipeline(
        stages=[
            LoadStage(),
            CleanStage(),
            ValidateStage(),
            DeriveStage(),
            SaveStage(),
        ]
    )


def main():

    datasets = [
        "data/raw/All_GPUs.csv",
        "data/raw/amd-cpus.csv",
        "data/raw/Intel_CPUs.csv",
    ]

    pipeline = create_pipeline()

    result = pipeline.run(datasets)

    print("\n" + "=" * 60)
    print("Pipeline finished")
    print("=" * 60)

    print(result)


if __name__ == "__main__":
    main()
