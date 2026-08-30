import logging

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Pipeline
from backend.rag.data_pipelines.stages.clean import CleanAndTagStage
from backend.rag.data_pipelines.stages.derive import DeriveCategoriesBrandsAttributesStage
from backend.rag.data_pipelines.stages.load import LoadRawFilesStage
from backend.rag.data_pipelines.stages.validate import ValidateRecordsStage
from backend.rag.data_pipelines.stages.write import WriteStructuredJsonStage

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s"
)


def build_pipeline() -> Pipeline[DataPipelineContext]:
    return Pipeline(
        [
            LoadRawFilesStage(),
            CleanAndTagStage(),
            ValidateRecordsStage(),
            DeriveCategoriesBrandsAttributesStage(),
            WriteStructuredJsonStage(),
        ]
    )


def main() -> None:
    pipeline = build_pipeline()
    result = pipeline.run(DataPipelineContext())

    print(f"\n{len(result.records)} records written across {len(result.written_files)} files.")
    for path in result.written_files:
        print(f"  - {path}")


if __name__ == "__main__":
    main()