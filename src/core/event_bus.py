"""Event bus for decoupled component communication."""

from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import logging
from typing import Any

from src.interfaces.ui import IEventBus

logger = logging.getLogger(__name__)


class EventBus(IEventBus):
    """Thread-safe event bus with sync/async publishing."""

    __slots__ = ("_executor", "_subscribers")

    def __init__(self, async_mode: bool = False, max_workers: int = 4):
        self._subscribers = defaultdict(list)
        self._executor = ThreadPoolExecutor(max_workers) if async_mode else None

    def subscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]) -> None:
        try:
            self._subscribers[event_type].remove(handler)
        except ValueError:
            pass

    def publish(self, event_type: str, data: Any = None) -> None:
        for handler in self._subscribers[event_type]:
            try:
                (self._executor.submit if self._executor else lambda f, d: f(d))(handler, data)
            except Exception:
                logger.exception(f"Handler error: {getattr(handler, '__name__', 'unknown')}")

    def clear(self) -> None:
        self._subscribers.clear()

    def shutdown(self) -> None:
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
