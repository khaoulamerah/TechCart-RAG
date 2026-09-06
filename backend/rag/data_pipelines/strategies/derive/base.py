from abc import ABC, abstractmethod
from typing import Any


class DeriveStrategy(ABC):

    @abstractmethod
    def derive(self, data: Any) -> Any:
        pass