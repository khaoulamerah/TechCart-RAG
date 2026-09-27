import logging
from collections.abc import AsyncIterator

from langchain_ollama import ChatOllama

from backend.rag.generator.base import (
    LLMProvider,
    LLMProviderError,
)


logger = logging.getLogger(
    "techcart.llm.ollama"
)


class OllamaLLMProvider(LLMProvider):
    """LLM provider implementation using Ollama."""

    def __init__(
        self,
        model: str,
        base_url: str,
    ) -> None:
        if not model:
            raise ValueError(
                "model cannot be empty."
            )

        if not base_url:
            raise ValueError(
                "base_url cannot be empty."
            )

        self.model = model
        self.base_url = base_url

        self._client = ChatOllama(
            model=model,
            base_url=base_url,
        )

    def generate_stream(
        self,
        prompt: str,
    ) -> AsyncIterator[str]:
        """Stream the LLM response."""

        async def stream() -> AsyncIterator[str]:
            try:
                async for chunk in self._client.astream(
                    prompt
                ):
                    content = chunk.content or ""

                    if content:
                        yield content

            except Exception as exc:
                logger.exception(
                    "Ollama streaming request failed "
                    "(model=%s)",
                    self.model,
                )

                raise LLMProviderError(
                    "Could not stream response from Ollama "
                    f"(model '{self.model}'): {exc}"
                ) from exc

        return stream()