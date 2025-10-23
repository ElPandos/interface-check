"""Tool interface for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from typing import Any


class IParser(ABC):
    """Abstract interface for parsers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""

    @abstractmethod
    def result(self) -> dict[str, Any]:  # hmm what here?
        """Get parsed result."""

    @abstractmethod
    def log(self, command: str) -> None:
        """Log info."""
