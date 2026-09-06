import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)

from backend.rag.data_pipelines.strategies.validate.base import (
    ValidationStrategy,
)


class CsvValidationStrategy(ValidationStrategy):

    def validate(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("Validating CSV data...")

        for item in data:

            source: str = item["source"]
            df: pd.DataFrame = item["data"]

            print("\n" + "=" * 60)
            print(f"Validating: {source}")
            print("=" * 60)

            # Check DataFrame is not empty
            if df.empty:

                raise ValueError(
                    f"Dataset is empty: {source}"
                )

            # Check columns exist
            if len(df.columns) == 0:

                raise ValueError(
                    f"Dataset has no columns: {source}"
                )

            # Check column names
            if any(
                not column.strip()
                for column in df.columns
            ):

                raise ValueError(
                    f"Empty column name found: {source}"
                )

            # Check completely empty rows
            empty_rows: int = (
                df.isna()
                .all(axis=1)
                .sum()
            )

            if empty_rows > 0:

                raise ValueError(
                    f"Dataset still contains "
                    f"{empty_rows} empty rows: "
                    f"{source}"
                )

            print("Validation passed.")
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")

        return data