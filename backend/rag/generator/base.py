from abc import ABC, abstractmethod


class LLMProviderError(Exception):
    """Raised when an LLM provider fails."""


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, message: str) -> str:
        raise NotImplementedError
