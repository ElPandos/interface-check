"""Event bus implementation for decoupled component communication."""

from collections import defaultdict
from collections.abc import Callable
import logging
from typing import Any

from src.interfaces.ui import IEventBus

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """Simple event bus for component communication."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Subscribe to event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed to {event_type}: {handler.__name__}")

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed from {event_type}: {handler.__name__}")
            except ValueError:
                logger.warning(f"Handler not found for {event_type}: {handler.__name__}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish event to subscribers."""
        handlers = self._subscribers.get(event_type, [])
        logger.debug(f"Publishing {event_type} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                handler(data)
            except Exception:
                logger.exception(f"Error in event handler for {event_type}")

    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscribers.clear()
        logger.debug("Event bus cleared")
