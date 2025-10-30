"""Tool interface for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
import logging
from typing import Any


class IParser(ABC):
    """Abstract interface for parsers."""

    def __init__(self, log_name: str):
        self._logger = logging.getLogger(log_name)

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""

    @abstractmethod
    def result(self) -> list[Any]:
        """Get parsed result."""

    @abstractmethod
    def log(self) -> None:
        """Log info."""
