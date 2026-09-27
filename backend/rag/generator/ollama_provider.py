import logging
from collections.abc import AsyncIterator

import httpx
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

        self.base_url = (
            base_url.rstrip("/")
        )

        self._client = ChatOllama(
            model=model,
            base_url=self.base_url,
        )

    async def warm_up(self) -> None:
        """
        Load the configured Ollama model into memory.

        This is executed during FastAPI startup so the
        first user request does not pay the model-loading cost.
        """

        url = (
            f"{self.base_url}/api/generate"
        )

        logger.info(
            "Warming up Ollama model '%s'...",
            self.model,
        )

        try:

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=180.0,
                    write=30.0,
                    pool=30.0,
                )
            ) as client:

                response = await client.post(
                    url,
                    json={
                        "model": self.model,
                        "prompt": "Reply with OK.",
                        "stream": False,
                        "keep_alive": "10m",
                        "options": {
                            "num_predict": 1,
                            "temperature": 0,
                        },
                    },
                )

                response.raise_for_status()

        except Exception as exc:

            logger.exception(
                "Ollama warm-up failed."
            )

            raise LLMProviderError(
                "Could not warm up Ollama "
                f"model '{self.model}': {exc}"
            ) from exc

        logger.info(
            "Ollama model '%s' is ready.",
            self.model,
        )

    def generate_stream(
        self,
        prompt: str,
    ) -> AsyncIterator[str]:
        """Stream the LLM response."""

        async def stream() -> AsyncIterator[str]:

            try:

                async for chunk in (
                    self._client.astream(
                        prompt
                    )
                ):

                    content = (
                        chunk.content or ""
                    )

                    if content:
                        yield content

            except Exception as exc:

                logger.exception(
                    "Ollama streaming request failed "
                    "(model=%s)",
                    self.model,
                )

                raise LLMProviderError(
                    "Could not stream response from "
                    f"Ollama (model '{self.model}'): "
                    f"{exc}"
                ) from exc

        return stream()