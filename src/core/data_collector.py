"""Independent data collection system with minimal dependencies."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime as dt
import logging
import queue
import threading
import time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class Sample[T]:
    """Generic data sample with timestamp."""

    timestamp: dt
    data: T
    source: str
    metadata: dict[str, Any] | None = None


class DataSource[T](ABC):
    """Abstract data source interface."""

    @abstractmethod
    def collect(self) -> T:
        """Collect data from source."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Source identifier."""


class DataCollector[T]:
    """Independent data collector with configurable sources."""

    def __init__(self, source: DataSource[T], interval: float = 1.0):
        self._source = source
        self._interval = interval
        self._samples: queue.Queue[Sample[T]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._error_callback: Callable[[Exception], None] | None = None

    def set_error_callback(self, callback: Callable[[Exception], None]) -> None:
        """Set callback for error handling."""
        self._error_callback = callback

    def start(self) -> None:
        """Start data collection."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.debug(f"Started collector for {self._source.name}")

    def stop(self) -> None:
        """Stop data collection."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.debug(f"Stopped collector for {self._source.name}")

    def get_samples(self, max_count: int | None = None) -> list[Sample[T]]:
        """Get collected samples."""
        samples = []
        count = 0
        while not self._samples.empty() and (max_count is None or count < max_count):
            try:
                samples.append(self._samples.get_nowait())
                count += 1
            except queue.Empty:
                break
        return samples

    def get_latest(self) -> Sample[T] | None:
        """Get most recent sample."""
        samples = self.get_samples(1)
        return samples[0] if samples else None

    def _collect_loop(self) -> None:
        """Main collection loop."""
        while not self._stop_event.is_set():
            try:
                data = self._source.collect()
                sample = Sample(timestamp=dt.now(tz=UTC), data=data, source=self._source.name)
                self._samples.put(sample)

            except Exception as e:
                logger.exception(f"Collection error from {self._source.name}")
                if self._error_callback:
                    self._error_callback(e)

            time.sleep(self._interval)


class CollectorManager:
    """Manages multiple data collectors."""

    def __init__(self):
        self._collectors: dict[str, DataCollector] = {}

    def add_collector(self, name: str, collector: DataCollector) -> None:
        """Add collector to manager."""
        if name in self._collectors:
            self._collectors[name].stop()
        self._collectors[name] = collector

    def start_all(self) -> None:
        """Start all collectors."""
        for collector in self._collectors.values():
            collector.start()

    def stop_all(self) -> None:
        """Stop all collectors."""
        for collector in self._collectors.values():
            collector.stop()

    def get_collector(self, name: str) -> DataCollector | None:
        """Get collector by name."""
        return self._collectors.get(name)

    def remove_collector(self, name: str) -> None:
        """Remove and stop collector."""
        if name in self._collectors:
            self._collectors[name].stop()
            del self._collectors[name]

    def clear(self) -> None:
        """Stop and remove all collectors."""
        self.stop_all()
        self._collectors.clear()
