"""Event bus implementation for decoupled component communication."""

from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any

from src.interfaces.ui import IEventBus

logger = logging.getLogger(__name__)


class HybridEventBus(IEventBus):
    """
    Event bus supporting both synchronous and asynchronous event publishing.

    - Thread-safe for concurrent publishing.
    - Supports unsubscribe and graceful shutdown.
    """

    def __init__(self, async_mode: bool = False, max_workers: int = 4):
        self._subscribers = defaultdict(list)
        self._async_mode = async_mode
        self._executor = ThreadPoolExecutor(max_workers=max_workers) if async_mode else None

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Subscribe a handler to an event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed: {handler.__name__} to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        """Unsubscribe a handler from an event type."""
        try:
            self._subscribers[event_type].remove(handler)
        except (KeyError, ValueError):
            logger.warning(f"Handler not found for {event_type}: {handler.__name__}")

    def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers."""
        handlers = self._subscribers.get(event_type, [])
        logger.debug(f"Publishing {event_type} to {len(handlers)} handlers")

        for handler in handlers:
            try:
                if self._async_mode and self._executor:
                    self._executor.submit(handler, data)
                else:
                    handler(data)
            except Exception:
                logger.exception(f"Error in handler {handler.__name__} for {event_type}")

    def clear(self) -> None:
        """Clear all event subscriptions."""
        self._subscribers.clear()
        logger.debug("All event handlers cleared")

    def shutdown(self) -> None:
        """Shutdown thread pool gracefully (if in async mode)."""
        if self._executor:
            self._executor.shutdown(wait=True)
            logger.debug("Event bus executor shut down")
