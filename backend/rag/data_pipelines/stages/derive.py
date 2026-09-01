import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)


class DeriveStage(Stage):

    def run(self, data: PipelineData) -> PipelineData:

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


class MarkdownDeriveStage(Stage):

    def run(self, data: PipelineData) -> PipelineData:

        print("Deriving Markdown data...")

        for item in data:

            source: str = item["source"]
            content: str = item["content"]

            print("\n" + "=" * 60)
            print(f"Deriving: {source}")
            print("=" * 60)

            # Extract title
            title: str | None = None

            for line in content.splitlines():

                line = line.strip()

                if line.startswith("# "):

                    title = line[2:].strip()

                    break

            item["title"] = title

            # Extract sections
            sections: list[str] = []

            for line in content.splitlines():

                line = line.strip()

                if line.startswith("## "):

                    section: str = line[3:].strip()

                    sections.append(section)

            item["sections"] = sections

            print(f"Title: {title}")
            print(
                f"Sections found: "
                f"{len(sections)}"
            )

        return data