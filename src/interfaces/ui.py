"""UI component interfaces for loose coupling."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class IComponent(ABC):
    """Abstract interface for UI components."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Component name identifier.

        Returns:
            Component name
        """

    @abstractmethod
    def build(self) -> None:
        """Build the UI component."""

    @abstractmethod
    def destroy(self) -> None:
        """Clean up component resources."""


class ITab(IComponent):
    """Interface for tab components."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Tab display label.

        Returns:
            Tab label
        """

    @property
    @abstractmethod
    def icon(self) -> str:
        """Tab icon identifier.

        Returns:
            Icon name
        """


class IPanel(IComponent):
    """Interface for panel components."""

    @abstractmethod
    def refresh(self) -> None:
        """Refresh panel content."""


class IEventBus(ABC):
    """Event bus for decoupled component communication."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Subscribe to event type.

        Args:
            event_type: Event type identifier
            handler: Event handler function
        """

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe from event type.

        Args:
            event_type: Event type identifier
            handler: Event handler function
        """

    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish event to subscribers.

        Args:
            event_type: Event type identifier
            data: Event data
        """

    @abstractmethod
    def clear(self) -> None:
        """Clear all event subscriptions."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown thread pool gracefully (if in async mode)."""
