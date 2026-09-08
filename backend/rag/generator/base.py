from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProviderError(Exception):
    """Raised when an LLM provider fails."""


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate_stream(self, message: str) -> AsyncIterator[str]:
        raise NotImplementedError