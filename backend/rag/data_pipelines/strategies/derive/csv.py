import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)

from backend.rag.data_pipelines.strategies.derive.base import (
    DeriveStrategy,
)


class CsvDeriveStrategy(DeriveStrategy):

    def derive(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("Deriving CSV data...")

        for item in data:

            source: str = item["source"]
            df: pd.DataFrame = item["data"]

            print("\n" + "=" * 60)
            print(f"Deriving: {source}")
            print("=" * 60)

            def row_to_text(row: pd.Series) -> str:

                parts: list[str] = []

                for column, value in row.items():

                    if value is not None:

                        value = str(value).strip()

                        if value:
                            parts.append(
                                f"{column}: {value}"
                            )

                return ". ".join(parts)

            df["text"] = df.apply(
                row_to_text,
                axis=1,
            )

            print("Created 'text' column.")
            print(f"Rows: {len(df)}")

        return data