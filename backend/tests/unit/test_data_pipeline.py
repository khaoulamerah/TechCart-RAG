import pandas as pd

from backend.rag.data_pipelines.context import DataPipelineContext
from backend.rag.data_pipelines.core import Pipeline
from backend.rag.data_pipelines.stages.clean import CleanAndTagStage, guess_brand
from backend.rag.data_pipelines.stages.derive import (
    DeriveCategoriesBrandsAttributesStage,
)
from backend.rag.data_pipelines.stages.validate import ValidateRecordsStage


def test_guess_brand_matches_known_keyword():
    assert guess_brand("NVIDIA GeForce RTX 4090", ["NVIDIA", "AMD"]) == "NVIDIA"


def test_guess_brand_returns_none_when_no_match():
    assert guess_brand("Some Unknown Card", ["NVIDIA", "AMD"]) is None


def test_clean_and_tag_stage_builds_records_from_a_fake_dataframe():
    # No CSV file needed — we hand-build the "raw" input directly.
    df = pd.DataFrame({"Name": ["NVIDIA RTX 4090"], "VRAM": [24]})
    context = DataPipelineContext()
    context.raw["fake_gpus.csv"] = (
        df,
        {"category": "gpu", "brands": ["NVIDIA", "AMD"]},
    )

    result = CleanAndTagStage().run(context)

    assert len(result.records) == 1
    assert result.records[0]["brand"] == "NVIDIA"
    assert result.records[0]["category"] == "GPU"
    assert "vram" in result.records[0]["specs"]


def test_validate_stage_drops_records_missing_required_fields():
    context = DataPipelineContext()
    context.records = [
        {"id": "1", "name": "Valid Product", "category": "GPU"},
        {"id": "2", "name": None, "category": "GPU"},  # missing name -> dropped
    ]

    result = ValidateRecordsStage().run(context)

    assert len(result.records) == 1
    assert result.records[0]["id"] == "1"


def test_derive_stage_computes_categories_and_brands():
    context = DataPipelineContext()
    context.records = [
        {"id": "1", "category": "GPU", "brand": "NVIDIA", "specs": {"vram": 24}},
        {"id": "2", "category": "CPU", "brand": "Intel", "specs": {"cores": 8}},
    ]

    result = DeriveCategoriesBrandsAttributesStage().run(context)

    assert result.categories == ["CPU", "GPU"]
    assert result.brands == ["Intel", "NVIDIA"]
    assert result.attributes["GPU"] == ["vram"]


def test_full_pipeline_end_to_end_with_fake_input():
    """Integration test: the same stages, chained through a real Pipeline."""
    df = pd.DataFrame({"Name": ["Intel Core i7-13700K"], "Cores": [16]})
    context = DataPipelineContext()
    context.raw["fake_cpus.csv"] = (df, {"category": "cpu", "brands": ["Intel"]})

    pipeline = Pipeline(
        [
            CleanAndTagStage(),
            ValidateRecordsStage(),
            DeriveCategoriesBrandsAttributesStage(),
        ]
    )
    result = pipeline.run(context)

    assert len(result.records) == 1
    assert result.categories == ["CPU"]
    assert result.brands == ["Intel"]
