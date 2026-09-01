from abc import ABC, abstractmethod
from typing import Any


FilePaths = list[str]

PipelineData = list[dict[str, Any]]


class Stage(ABC):

    @abstractmethod
    def run(self, data: Any) -> Any:
        pass