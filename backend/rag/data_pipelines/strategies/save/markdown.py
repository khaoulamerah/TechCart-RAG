from backend.rag.data_pipelines.strategies.cleaning.base import (
    CleaningStrategy,
)


class MarkdownCleaningStrategy(CleaningStrategy):

    def clean(self, data: str) -> str:

        content = data

        print("Cleaning Markdown data...")

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

        print(
            f"Characters after cleaning: "
            f"{len(content)}"
        )

        return content