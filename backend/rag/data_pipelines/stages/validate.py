from backend.rag.data_pipelines.stages.base import Stage


class ValidateStage(Stage):
    def run(self, data):

        print("Validating CSV data...")

        for item in data:

            source = item["source"]
            df = item["data"]

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
            if any(not column.strip() for column in df.columns):
                raise ValueError(
                    f"Empty column name found: {source}"
                )

            # Check completely empty rows
            empty_rows = df.isna().all(axis=1).sum()

            if empty_rows > 0:
                raise ValueError(
                    f"Dataset still contains "
                    f"{empty_rows} empty rows: {source}"
                )

            print("Validation passed.")
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")

        return data


class MarkdownValidateStage(Stage):
    def run(self, data):

        print("Validating Markdown data...")

        for item in data:

            source = item["source"]
            content = item["content"]

            print("\n" + "=" * 60)
            print(f"Validating: {source}")
            print("=" * 60)

            # Check content exists
            if not content:
                raise ValueError(
                    f"Markdown document is empty: {source}"
                )

            # Check content is a string
            if not isinstance(content, str):
                raise TypeError(
                    f"Markdown content must be a string: {source}"
                )

            # Remove surrounding whitespace for validation
            content = content.strip()

            # Check again after stripping
            if not content:
                raise ValueError(
                    f"Markdown document contains only whitespace: {source}"
                )

            print("Validation passed.")
            print(f"Characters: {len(content)}")

        return data