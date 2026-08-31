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

    for dataset in datasets:

        print("\n" + "=" * 60)
        print(f"Processing: {dataset}")
        print("=" * 60)

        pipeline = create_pipeline()

        result = pipeline.run(dataset)

        print("Pipeline finished")
        print(result)


if __name__ == "__main__":
    main()