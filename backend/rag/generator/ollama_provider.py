import logging

from langchain_ollama import ChatOllama

from backend.rag.generator.base import LLMProvider, LLMProviderError

logger = logging.getLogger("techcart.llm.ollama")


class OllamaLLMProvider(LLMProvider):
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url
        # LangChain's client is created once and reused — see the
        # factory below, which caches this instance.
        self._client = ChatOllama(model=model, base_url=base_url)

    async def generate(self, message: str) -> str:
        try:
            response = await self._client.ainvoke(message)
        except Exception as exc:
            logger.error("Ollama request failed (model=%s): %s", self.model, exc)
            raise LLMProviderError(
                f"Could not get a response from Ollama (model '{self.model}'): {exc}"
            ) from exc

        content = (response.content or "").strip()
        if not content:
            raise LLMProviderError(
                f"Ollama (model '{self.model}') returned an empty response."
            )
        return content
