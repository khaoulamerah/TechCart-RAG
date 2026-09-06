from backend.rag.data_pipelines.pipeline import Pipeline

from backend.rag.data_pipelines.stages.clean import CleanStage

from backend.rag.data_pipelines.stages.derive import (
    DeriveStage,
)

from backend.rag.data_pipelines.stages.load import (
    LoadStage,
)

from backend.rag.data_pipelines.stages.save import (
    SaveStage,
)

from backend.rag.data_pipelines.stages.validate import (
    ValidateStage,
)

from backend.rag.data_pipelines.stages.base import FilePaths

from backend.rag.data_pipelines.strategies.cleaning.csv import (
    CsvCleaningStrategy,
)

from backend.rag.data_pipelines.strategies.cleaning.markdown import (
    MarkdownCleaningStrategy,
)

from backend.rag.data_pipelines.strategies.loading.csv import (
    CsvLoadingStrategy,
)

from backend.rag.data_pipelines.strategies.loading.markdown import (
    MarkdownLoadingStrategy,
)

from backend.rag.data_pipelines.strategies.derive.csv import (
    CsvDeriveStrategy,
)

from backend.rag.data_pipelines.strategies.derive.markdown import (
    MarkdownDeriveStrategy,
)

from backend.rag.data_pipelines.strategies.validate.csv import (
    CsvValidationStrategy,
)

from backend.rag.data_pipelines.strategies.validate.markdown import (
    MarkdownValidationStrategy,
)

from backend.rag.data_pipelines.strategies.save.csv import (
    CsvSaveStrategy,
)

from backend.rag.data_pipelines.strategies.save.markdown import (
    MarkdownSaveStrategy,
)

def create_csv_pipeline() -> Pipeline:

    loading_strategy = CsvLoadingStrategy()
    cleaning_strategy = CsvCleaningStrategy()
    validation_strategy = CsvValidationStrategy()
    derive_strategy = CsvDeriveStrategy()
    save_strategy = CsvSaveStrategy()

    return Pipeline(
        stages=[
            LoadStage(loading_strategy),
            CleanStage(cleaning_strategy),
            ValidateStage(validation_strategy),
            DeriveStage(derive_strategy),
            SaveStage(save_strategy),
        ]
    )


def create_markdown_pipeline() -> Pipeline:

    loading_strategy = MarkdownLoadingStrategy()
    cleaning_strategy = MarkdownCleaningStrategy()
    validation_strategy = MarkdownValidationStrategy()
    derive_strategy = MarkdownDeriveStrategy()
    save_strategy = MarkdownSaveStrategy()

    return Pipeline(
        stages=[
            LoadStage(loading_strategy),
            CleanStage(cleaning_strategy),
            ValidateStage(validation_strategy),
            DeriveStage(derive_strategy),
            SaveStage(save_strategy),
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

    csv_pipeline: Pipeline = create_csv_pipeline()

    csv_result = csv_pipeline.run(csv_datasets)

    print("\n" + "=" * 60)
    print("CSV PIPELINE RESULT")
    print("=" * 60)

    print(csv_result)

    # MARKDOWN PIPELINE

    print("\n" + "=" * 60)
    print("STARTING MARKDOWN PIPELINE")
    print("=" * 60)

    markdown_pipeline: Pipeline = create_markdown_pipeline()

    markdown_result = markdown_pipeline.run(
        markdown_datasets
    )

    print("\n" + "=" * 60)
    print("MARKDOWN PIPELINE RESULT")
    print("=" * 60)

    print(markdown_result)


if __name__ == "__main__":
    main()