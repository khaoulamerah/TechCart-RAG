from backend.rag.data_pipelines.stages.base import Stage


class CleanStage(Stage):
    def run(self, data):

        print("Cleaning CSV data...")

        for item in data:
            source = item["source"]
            df = item["data"]

            print("\n" + "=" * 60)
            print(f"Cleaning: {source}")
            print("=" * 60)

            # Before cleaning
            print(f"Rows before cleaning: {len(df)}")
            print(f"Columns before cleaning: {len(df.columns)}")

            # Remove empty rows
            before_rows = len(df)

            df.dropna(how="all", inplace=True)

            after_rows = len(df)

            print(f"Empty rows removed: {before_rows - after_rows}")

            # Remove empty columns
            before_columns = len(df.columns)

            df.dropna(axis=1, how="all", inplace=True)

            after_columns = len(df.columns)

            print(f"Empty columns removed: {before_columns - after_columns}")

            # Normalize column names
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(" ", "_", regex=False)
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

            print(f"String columns cleaned: {len(string_columns)}")

            print(f"Rows after cleaning: {len(df)}")
            print(f"Columns after cleaning: {len(df.columns)}")

        return data


class MarkdownCleanStage(Stage):
    def run(self, data):

        print("Cleaning Markdown data...")

        for item in data:

            source = item["source"]
            content = item["content"]

            print("\n" + "=" * 60)
            print(f"Cleaning: {source}")
            print("=" * 60)

            # Before cleaning
            print(f"Characters before cleaning: {len(content)}")

            # Normalize line endings
            content = content.replace("\r\n", "\n")
            content = content.replace("\r", "\n")

            # Remove spaces/tabs at the beginning and end of lines
            lines = []

            for line in content.split("\n"):
                line = line.strip()
                lines.append(line)

            # Remove excessive blank lines
            cleaned_lines = []

            previous_blank = False

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

            print(f"Characters after cleaning: {len(content)}")

        return data