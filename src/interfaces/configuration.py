"""Configuration interface for abstracting config management."""

from abc import ABC, abstractmethod
from typing import Any


class IConfigurationProvider(ABC):
    """Abstract interface for configuration providers."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """

    @abstractmethod
    def save(self) -> None:
        """Save configuration state."""

    @abstractmethod
    def reload(self) -> None:
        """Reload configuration state from source."""

    @abstractmethod
    def get_section(self, section: str) -> dict[str, Any]:
        """Get configuration section.

        Args:
            section: Section name

        Returns:
            Section dictionary
        """


class IConfigurationFactory(ABC):
    """Factory for creating configuration providers."""

    @abstractmethod
    def create_provider(self, source: str) -> IConfigurationProvider:
        """Create configuration provider from source.

        Args:
            source: Configuration source

        Returns:
            Configuration provider instance
        """
