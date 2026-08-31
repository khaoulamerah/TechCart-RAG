from backend.rag.data_pipelines.stages.base import Stage


class DeriveStage(Stage):

    def run(self, data):

        print("Deriving data...")

        for item in data:

            source = item["source"]
            df = item["data"]

            print("\n" + "=" * 60)
            print(f"Deriving: {source}")
            print("=" * 60)

            def row_to_text(row):

                parts = []

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
                axis=1
            )

            print("Created 'text' column.")
            print(f"Rows: {len(df)}")

        return data