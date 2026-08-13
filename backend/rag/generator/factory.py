from functools import lru_cache

from backend.config.settings import settings
from backend.rag.generator.base import LLMProvider
from backend.rag.generator.ollama_provider import (
    OllamaLLMProvider,
)


@lru_cache
def get_llm_provider() -> LLMProvider:

    provider = settings.LLM_PROVIDER.lower().strip()

    if provider == "ollama":
        return OllamaLLMProvider(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )

    raise ValueError(
        f"Unknown LLM_PROVIDER '{settings.LLM_PROVIDER}'. "
        "Supported providers: 'ollama'."
    )