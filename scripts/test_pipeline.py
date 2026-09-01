from backend.rag.data_pipelines.pipeline import Pipeline

from backend.rag.data_pipelines.stages.clean import CleanStage
from backend.rag.data_pipelines.stages.derive import DeriveStage
from backend.rag.data_pipelines.stages.load import (
    LoadStage,
    MarkdownLoadStage,
)
from backend.rag.data_pipelines.stages.save import SaveStage
from backend.rag.data_pipelines.stages.validate import ValidateStage


def create_csv_pipeline():

    return Pipeline(
        stages=[
            LoadStage(),
            CleanStage(),
            ValidateStage(),
            DeriveStage(),
            SaveStage(),
        ]
    )


def create_markdown_pipeline():

    return Pipeline(
        stages=[
            MarkdownLoadStage(),
            CleanStage(),
            ValidateStage(),
            SaveStage(),
        ]
    )


def main():

    csv_datasets = [
        "data/raw/All_GPUs.csv",
        "data/raw/amd-cpus.csv",
        "data/raw/Intel_CPUs.csv",
    ]

    markdown_documents = [
        "data/semi_structured/documentation/store_info.md",
        "data/semi_structured/faq/faq.md",
        "data/semi_structured/guides/gpu_buying_guide.md",
        "data/semi_structured/policies/payment_policy.md",
        "data/semi_structured/policies/return_policy.md",
        "data/semi_structured/policies/shipping_policy.md",
        "data/semi_structured/policies/warranty_policy.md",
    ]

    # ==========================================================
    # CSV PIPELINE
    # ==========================================================

    print("\n" + "=" * 60)
    print("STARTING CSV PIPELINE")
    print("=" * 60)

    csv_pipeline = create_csv_pipeline()

    csv_result = csv_pipeline.run(csv_datasets)

    print("\n" + "=" * 60)
    print("CSV PIPELINE FINISHED")
    print("=" * 60)

    print(csv_result)

    # ==========================================================
    # MARKDOWN PIPELINE
    # ==========================================================

    print("\n" + "=" * 60)
    print("STARTING MARKDOWN PIPELINE")
    print("=" * 60)

    markdown_pipeline = create_markdown_pipeline()

    markdown_result = markdown_pipeline.run(markdown_documents)

    print("\n" + "=" * 60)
    print("MARKDOWN PIPELINE FINISHED")
    print("=" * 60)

    print(markdown_result)

    # ==========================================================
    # ALL PIPELINES FINISHED
    # ==========================================================

    print("\n" + "=" * 60)
    print("ALL DATA PIPELINES FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()