import pandas as pd

from backend.rag.data_pipelines.strategies.cleaning.base import (
    CleaningStrategy,
)


class CsvCleaningStrategy(CleaningStrategy):

    def clean(self, data: pd.DataFrame) -> pd.DataFrame:

        print("Cleaning CSV data...")

        df = data.copy()

        # Before cleaning
        print(f"Rows before cleaning: {len(df)}")
        print(f"Columns before cleaning: {len(df.columns)}")

        # Remove empty rows

        before_rows: int = len(df)

        df.dropna(
            how="all",
            inplace=True,
        )

        after_rows: int = len(df)

        print(
            f"Empty rows removed: "
            f"{before_rows - after_rows}"
        )

        # Remove empty columns

        before_columns: int = len(df.columns)

        df.dropna(
            axis=1,
            how="all",
            inplace=True,
        )

        after_columns: int = len(df.columns)

        print(
            f"Empty columns removed: "
            f"{before_columns - after_columns}"
        )

        # Normalize column names

        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(
                " ",
                "_",
                regex=False,
            )
        )

        print("Column names normalized.")

        # Clean string values

        string_columns = df.select_dtypes(
            include=["object", "string"]
        ).columns

        for column in string_columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

        print(
            f"String columns cleaned: "
            f"{len(string_columns)}"
        )

        print(f"Rows after cleaning: {len(df)}")
        print(
            f"Columns after cleaning: "
            f"{len(df.columns)}"
        )

        return df