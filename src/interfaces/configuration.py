"""Configuration interface for abstracting config management."""

from abc import ABC, abstractmethod
from typing import Any


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
        """Save configuration state."""

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration state from source."""

    @abstractmethod
    def get_section(self, section: str) -> dict[str, Any]:
        """Get configuration section."""


class IConfigurationFactory(ABC):
    """Factory for creating configuration providers."""

    @abstractmethod
    def create_provider(self, source: str) -> IConfigurationProvider:
        """Create configuration provider from source."""
