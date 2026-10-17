import os
from pathlib import Path

from backend.rag.data_pipelines.pipeline import Pipeline
from backend.rag.data_pipelines.stages.base import FilePaths
from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.load import LoadStage
from backend.rag.data_pipelines.stages.save import SaveStage
from backend.rag.data_pipelines.stages.validate import ValidateStage
from backend.rag.data_pipelines.utils import DataType


PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


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
    os.chdir(PROJECT_ROOT)

    markdown_datasets: FilePaths = [
        "data/semi_structured/documentation/store_info.md",
        "data/semi_structured/faq/faq.md",
        "data/semi_structured/guides/gpu_buying_guide.md",
        "data/semi_structured/policies/payment_policy.md",
        "data/semi_structured/policies/return_policy.md",
        "data/semi_structured/policies/shipping_policy.md",
        "data/semi_structured/policies/warranty_policy.md",
    ]

    print(
        "\n" + "=" * 70
    )
    print(
        "STARTING MARKDOWN DATA PIPELINE"
    )
    print(
        "=" * 70
    )

    pipeline = create_pipeline()

    pipeline.set_datatype(
        DataType.MD
    )

    result = pipeline.run(
        markdown_datasets
    )

    print(
        "\n" + "=" * 70
    )
    print(
        "MARKDOWN PIPELINE COMPLETED"
    )
    print(
        "=" * 70
    )

    print(
        f"Processed documents: {len(result)}"
    )


if __name__ == "__main__":
    main()