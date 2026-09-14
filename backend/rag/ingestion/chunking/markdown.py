import re

from backend.rag.ingestion.chunking.base import ChunkingStrategy
from backend.rag.ingestion.document import Chunk, Document


class MarkdownChunkingStrategy(ChunkingStrategy):

    def __init__(
        self,
        chunk_size: int = 1000,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        self.chunk_size = chunk_size

    # Public API
   
    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:

        content = document.content.strip()

        if not content:
            return []

        sections = self._split_into_sections(content)

        chunks: list[Chunk] = []

        for section in sections:
            section_chunks = self._process_section(
                section
            )

            chunks.extend(section_chunks)

        return self._add_metadata(
            chunks=chunks,
            document=document,
        )

    # Markdown section parsing
    def _split_into_sections(
        self,
        content: str,
    ) -> list[str]:

        lines = content.splitlines()

        sections: list[str] = []
        current_section: list[str] = []

        for line in lines:

            if self._is_heading(line):

                if current_section:
                    section = self._clean_text(
                        "\n".join(current_section)
                    )

                    if section:
                        sections.append(section)

                current_section = [line]

            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section = self._clean_text(
                "\n".join(current_section)
            )

            if section:
                sections.append(section)

        return sections


    # Section processing
    def _process_section(
        self,
        section: str,
    ) -> list[str]:

        if self._contains_faq(section):
            return self._chunk_faq_section(
                section
            )

        if self._contains_table(section):
            return self._chunk_table_section(
                section
            )

        if self._contains_list(section):
            return self._chunk_list_section(
                section
            )

        if len(section) <= self.chunk_size:
            return [section]

        return self._split_large_section(
            section
        )

    # FAQ detection
    def _contains_faq(
        self,
        section: str,
    ) -> bool:

        return bool(
            re.search(
                r"^\s*\*\*.+?\?\*\*\s*$",
                section,
                re.MULTILINE,
            )
        )

    def _chunk_faq_section(
        self,
        section: str,
    ) -> list[str]:

        lines = section.splitlines()

        heading: str | None = None
        faq_units: list[str] = []

        current_question: str | None = None
        current_answer: list[str] = []

        for line in lines:

            stripped = line.strip()

            # Markdown heading
            if self._is_heading(line):

                if current_question:
                    faq_units.append(
                        self._build_faq_unit(
                            current_question,
                            current_answer,
                        )
                    )

                    current_question = None
                    current_answer = []

                heading = stripped
                continue

            # FAQ question
            if self._is_faq_question(stripped):

                if current_question:
                    faq_units.append(
                        self._build_faq_unit(
                            current_question,
                            current_answer,
                        )
                    )

                current_question = stripped
                current_answer = []

                continue

            # Answer content
            if current_question:
                if stripped:
                    current_answer.append(
                        stripped
                    )

        # Add last FAQ
        if current_question:
            faq_units.append(
                self._build_faq_unit(
                    current_question,
                    current_answer,
                )
            )

        # If no FAQ was successfully parsed,
        # keep the original section.
        if not faq_units:
            return [section]

        chunks: list[str] = []

        for unit in faq_units:

            if heading:
                unit = (
                    f"{heading}\n\n"
                    f"{unit}"
                )

            if len(unit) <= self.chunk_size:
                chunks.append(unit)

            else:
                chunks.extend(
                    self._split_large_section(
                        unit
                    )
                )

        return chunks

    def _build_faq_unit(
        self,
        question: str,
        answer: list[str],
    ) -> str:

        answer_text = "\n".join(answer).strip()

        if answer_text:
            return (
                f"{question}\n"
                f"{answer_text}"
            )

        return question

    def _is_faq_question(
        self,
        line: str,
    ) -> bool:

        return bool(
            re.match(
                r"^\*\*.+?\?\*\*$",
                line,
            )
        )

    # Table handling
    def _contains_table(
        self,
        section: str,
    ) -> bool:
        """
        Detect a Markdown table.
        """

        lines = section.splitlines()

        table_lines = [
            line
            for line in lines
            if "|" in line
        ]

        return len(table_lines) >= 2

    def _chunk_table_section(
        self,
        section: str,
    ) -> list[str]:

        if len(section) <= self.chunk_size:
            return [section]

        return self._split_large_section(
            section
        )

    # List handling
    def _contains_list(
        self,
        section: str,
    ) -> bool:


        return bool(
            re.search(
                r"^\s*(?:[-*+]|\d+\.)\s+",
                section,
                re.MULTILINE,
            )
        )

    def _chunk_list_section(
        self,
        section: str,
    ) -> list[str]:

        if len(section) <= self.chunk_size:
            return [section]

        return self._split_large_section(
            section
        )

    # Large section splitting
    def _split_large_section(
        self,
        section: str,
    ) -> list[str]:

        paragraphs = re.split(
            r"\n\s*\n",
            section,
        )

        chunks: list[str] = []
        current: list[str] = []
        current_size = 0

        for paragraph in paragraphs:

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            paragraph_size = len(paragraph)

            # A single paragraph is already too large.
            if paragraph_size > self.chunk_size:

                if current:
                    chunks.append(
                        "\n\n".join(current)
                    )

                    current = []
                    current_size = 0

                chunks.extend(
                    self._split_long_text(
                        paragraph
                    )
                )

                continue

            additional_size = (
                paragraph_size
                if not current
                else paragraph_size + 2
            )

            if (
                current
                and current_size + additional_size
                > self.chunk_size
            ):
                chunks.append(
                    "\n\n".join(current)
                )

                current = []
                current_size = 0

            current.append(paragraph)

            current_size += (
                paragraph_size
                if current_size == 0
                else paragraph_size + 2
            )

        if current:
            chunks.append(
                "\n\n".join(current)
            )

        return chunks

    # Long text splitting
  
    def _split_long_text(
        self,
        text: str,
    ) -> list[str]:

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        chunks: list[str] = []
        current: list[str] = []
        current_size = 0

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_size = len(sentence)

            if (
                current
                and current_size
                + sentence_size
                + 1
                > self.chunk_size
            ):
                chunks.append(
                    " ".join(current)
                )

                current = []
                current_size = 0

            # If one sentence is itself larger than
            # chunk_size, split it directly.
            if sentence_size > self.chunk_size:

                if current:
                    chunks.append(
                        " ".join(current)
                    )

                    current = []
                    current_size = 0

                chunks.extend(
                    self._split_by_characters(
                        sentence
                    )
                )

                continue

            current.append(sentence)

            current_size += (
                sentence_size
                if current_size == 0
                else sentence_size + 1
            )

        if current:
            chunks.append(
                " ".join(current)
            )

        return chunks

    def _split_by_characters(
        self,
        text: str,
    ) -> list[str]:

        return [
            text[start : start + self.chunk_size]
            for start in range(
                0,
                len(text),
                self.chunk_size,
            )
        ]

    # Helpers
  
    def _is_heading(
        self,
        line: str,
    ) -> bool:

        return bool(
            re.match(
                r"^\s{0,3}#{1,6}\s+.+",
                line,
            )
        )

    def _clean_text(
        self,
        text: str,
    ) -> str:
 

        lines = [
            line.rstrip()
            for line in text.splitlines()
        ]

        return "\n".join(lines).strip()

    def _add_metadata(
        self,
        chunks: list[Chunk],
        document: Document,
    ) -> list[Chunk]:
  

        result: list[Chunk] = []

        for position, text in enumerate(chunks):

            result.append(
                Chunk(
                    id=(
                        f"{document.id}_"
                        f"chunk_{position:04d}"
                    ),
                    document_id=document.id,
                    text=text,
                    metadata={
                        **document.metadata,
                        "position": position,
                        "chunking_strategy": (
                            "markdown"
                        ),
                    },
                )
            )

        return result
