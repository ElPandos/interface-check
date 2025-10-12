"""UI component interfaces for loose coupling."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class IUIComponent(ABC):
    """Abstract interface for UI components."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Component name identifier."""

    @abstractmethod
    def build(self) -> None:
        """Build the UI component."""

    @abstractmethod
    def destroy(self) -> None:
        """Clean up component resources."""


class ITab(IUIComponent):
    """Interface for tab components."""

    @property
    @abstractmethod
    def label(self) -> str:
        """Tab display label."""

    @property
    @abstractmethod
    def icon(self) -> str:
        """Tab icon identifier."""


class IPanel(IUIComponent):
    """Interface for panel components."""

    @abstractmethod
    def refresh(self) -> None:
        """Refresh panel content."""


class IEventBus(ABC):
    """Event bus for decoupled component communication."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Subscribe to event type."""

    @abstractmethod
    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe from event type."""

    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish event to subscribers."""
