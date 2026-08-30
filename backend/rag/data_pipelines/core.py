from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

logger = logging.getLogger("techcart.pipeline")

T = TypeVar("T")


class Stage(ABC, Generic[T]):
    """One processing step. Subclasses implement run() only."""

    @abstractmethod
    def run(self, data: T) -> T:
        raise NotImplementedError


class Pipeline(Generic[T]):
    """Coordinates execution of an ordered list of Stages."""

    def __init__(self, stages: list[Stage[T]]):
        self.stages = stages

    def run(self, data: T) -> T:
        for stage in self.stages:
            logger.info("Running stage: %s", stage.__class__.__name__)
            data = stage.run(data)
        return data