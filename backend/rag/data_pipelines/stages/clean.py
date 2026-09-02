import pandas as pd

from backend.rag.data_pipelines.stages.base import (
    PipelineData,
    Stage,
)






class CSVCleanStage(Stage):

    def run(self, data: PipelineData) -> PipelineData:

        print("Cleaning CSV data...")

        for item in data:

            source: str = item["source"]
            df: pd.DataFrame = item["data"]

            print("\n" + "=" * 60)
            print(f"Cleaning: {source}")
            print("=" * 60)

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

        return data


class MarkdownCleanStage(Stage):

    def run(self, data: PipelineData) -> PipelineData:

        print("Cleaning Markdown data...")

        for item in data:

            source: str = item["source"]
            content: str = item["content"]

            print("\n" + "=" * 60)
            print(f"Cleaning: {source}")
            print("=" * 60)

            # Before cleaning
            print(
                f"Characters before cleaning: "
                f"{len(content)}"
            )

            # Normalize line endings
            content = content.replace(
                "\r\n",
                "\n",
            )

            content = content.replace(
                "\r",
                "\n",
            )

            # Remove spaces/tabs at the beginning
            # and end of lines
            lines: list[str] = []

            for line in content.split("\n"):

                line = line.strip()

                lines.append(line)

            # Remove excessive blank lines
            cleaned_lines: list[str] = []

            previous_blank: bool = False

            for line in lines:

                if line == "":

                    if not previous_blank:
                        cleaned_lines.append(line)

                    previous_blank = True

                else:

                    cleaned_lines.append(line)
                    previous_blank = False

            # Rebuild document
            content = "\n".join(cleaned_lines)

            # Remove whitespace at document boundaries
            content = content.strip()

            # Save cleaned content
            item["content"] = content

            print(
                f"Characters after cleaning: "
                f"{len(content)}"
            )

        return data