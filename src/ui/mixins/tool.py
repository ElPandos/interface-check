"""Tool template for software and other extracting tools."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class Tool(ABC):
    """Mixin providing common abstract methods for tools used in GUI."""

    def __init__(self):
        self.num_screens = 1
        self.screen_connections = {}
        self.content_container = None

    @abstractmethod
    def collect(self) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    @abstractmethod
    def parse(self, raw_data: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    @abstractmethod
    def value(self) -> Any:
        """Build individual screen content. Must be implemented by subclass."""

    @abstractmethod
    def export(self, full_path: Path) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    @abstractmethod
    def save(self) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    @abstractmethod
    def log(self) -> None:
        """Build individual screen content. Must be implemented by subclass."""
