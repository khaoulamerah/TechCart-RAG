import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.data_pipelines.pipeline import Pipeline
from backend.rag.data_pipelines.stages.base import FilePaths
from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.load import LoadStage
from backend.rag.data_pipelines.stages.save import SaveStage
from backend.rag.data_pipelines.stages.validate import ValidateStage
from backend.rag.data_pipelines.utils import DataType


def create_pipeline() -> Pipeline:

    return Pipeline(
        stages=[
            LoadStage(),
            CleanStage(),
            ValidateStage(),
            DeriveStage(),
            SaveStage(),
        ]
    )



def main() -> None:

    csv_datasets: FilePaths = [
        "data/raw/All_GPUs.csv",
        "data/raw/amd-cpus.csv",
        "data/raw/Intel_CPUs.csv",
    ]

    markdown_datasets: FilePaths = [
        "data/semi_structured/documentation/store_info.md",
        "data/semi_structured/faq/faq.md",
        "data/semi_structured/guides/gpu_buying_guide.md",
        "data/semi_structured/policies/payment_policy.md",
        "data/semi_structured/policies/return_policy.md",
        "data/semi_structured/policies/shipping_policy.md",
        "data/semi_structured/policies/warranty_policy.md",
    ]

    # CSV PIPELINE

    print("\n" + "=" * 60)
    print("STARTING CSV PIPELINE")
    print("=" * 60)

    pipeline: Pipeline = create_pipeline()
    pipeline.set_datatype(DataType.CSV)

    csv_result = pipeline.run(csv_datasets)

    print("\n" + "=" * 60)
    print("CSV PIPELINE RESULT")
    print("=" * 60)

    print(csv_result)

    # MARKDOWN PIPELINE

    print("\n" + "=" * 60)
    print("STARTING MARKDOWN PIPELINE")
    print("=" * 60)

    pipeline.set_datatype(DataType.MD)
    markdown_result = pipeline.run(
        markdown_datasets
    )

    print("\n" + "=" * 60)
    print("MARKDOWN PIPELINE RESULT")
    print("=" * 60)

    print(markdown_result)


if __name__ == "__main__":
    os.chdir(PROJECT_ROOT)
    main()