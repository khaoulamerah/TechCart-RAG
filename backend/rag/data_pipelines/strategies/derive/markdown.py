from backend.rag.data_pipelines.stages.base import (
    PipelineData,
)

from backend.rag.data_pipelines.strategies.derive.base import (
    DeriveStrategy,
)


class MarkdownDeriveStrategy(DeriveStrategy):

    def derive(
        self,
        data: PipelineData,
    ) -> PipelineData:

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