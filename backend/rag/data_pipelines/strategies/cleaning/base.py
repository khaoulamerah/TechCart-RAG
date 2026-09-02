from abc import ABC, abstractmethod
from typing import Any


class CleaningStrategy(ABC):

    @abstractmethod
    def clean(self, data: Any) -> Any:
        pass