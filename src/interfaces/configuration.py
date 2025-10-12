"""Configuration interface for abstracting config management."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class IConfigurationProvider(ABC):
    """Abstract interface for configuration providers."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""

    @abstractmethod
    def save(self) -> None:
        """Persist configuration changes."""

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration from source."""

    @abstractmethod
    def get_section(self, section: str) -> dict[str, Any]:
        """Get entire configuration section."""


class IConfigurationFactory(ABC):
    """Factory for creating configuration providers."""

    @abstractmethod
    def create_provider(self, source: str) -> IConfigurationProvider:
        """Create configuration provider from source."""
