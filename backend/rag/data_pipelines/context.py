from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class DataPipelineContext:
    # filename -> (raw dataframe, source config) — filled by LoadRawFilesStage
    raw: dict[str, tuple[pd.DataFrame, dict]] = field(default_factory=dict)

    # cleaned, tagged product records — filled by CleanAndTagStage
    records: list[dict[str, Any]] = field(default_factory=list)

    # derived outputs — filled by DeriveCategoriesBrandsAttributesStage
    categories: list[str] = field(default_factory=list)
    brands: list[str] = field(default_factory=list)
    attributes: dict[str, list[str]] = field(default_factory=dict)

    # filled by WriteStructuredJsonStage, useful for tests/logging
    written_files: list[Path] = field(default_factory=list)