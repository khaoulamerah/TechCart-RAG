from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)
from backend.rag.data_pipelines.strategies.validate.base import (
    ValidationStrategy,
)


class MarkdownValidationStrategy(ValidationStrategy):

    def validate(
        self,
        data: PipelineData,
    ) -> PipelineData:

        print("Validating Markdown data...")

        for item in data:

            source: str = item["source"]
            content: str = item["content"]

            print("\n" + "=" * 60)
            print(f"Validating: {source}")
            print("=" * 60)

            # Check content type first
            if not isinstance(content, str):

                raise TypeError(
                    f"Markdown content must be a "
                    f"string: {source}"
                )

            # Remove surrounding whitespace
            content = content.strip()

            # Check content is not empty
            if not content:

                raise ValueError(
                    f"Markdown document is empty: "
                    f"{source}"
                )

            print("Validation passed.")
            print(f"Characters: {len(content)}")

        return data