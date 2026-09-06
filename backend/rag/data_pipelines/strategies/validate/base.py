from abc import ABC, abstractmethod
from typing import Any


class ValidationStrategy(ABC):

    @abstractmethod
    def validate(self, data: Any) -> Any:
        pass