from backend.rag.data_pipelines.stages.base import Stage


class CleanStage(Stage):
    def run(self, data):

        print("Cleaning data...")

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
                df.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
            )

            print("Column names normalized.")

            # Clean string values
            string_columns = df.select_dtypes(include=["object", "string"]).columns

            for column in string_columns:
                df[column] = df[column].astype("string").str.strip()

            print(f"String columns cleaned: {len(string_columns)}")

            print(f"Rows after cleaning: {len(df)}")
            print(f"Columns after cleaning: {len(df.columns)}")

        return data
