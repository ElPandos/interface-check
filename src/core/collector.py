"""Independent data collection system with improved performance."""

from abc import ABC, abstractmethod
import contextlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
import logging
import queue
import threading
import time
from typing import Any, TypeVar

from src.core.base import Component, Observer, Result, Subject
from src.core.connection import Connection

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class Sample[T]:
    """Generic data sample."""

    timestamp: datetime
    data: T
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, data: T, source: str, metadata: dict[str, Any] | None = None) -> "Sample[T]":
        return cls(timestamp=datetime.now(UTC), data=data, source=source, metadata=metadata or {})


class DataCollector[T](ABC):
    """Abstract data collector interface."""

    @abstractmethod
    def collect(self) -> Result[T]:
        """Collect data sample."""

    @abstractmethod
    def get_source_name(self) -> str:
        """Get collector source name."""


class CommandCollector(DataCollector[str]):
    """Command-based data collector."""

    def __init__(self, connection: Connection, command: str, source_name: str):
        self._connection = connection
        self._command = command
        self._source_name = source_name

    def collect(self) -> Result[str]:
        """Execute command and return output."""
        result = self._connection.execute(self._command)
        if not result.success:
            return Result.fail(result.error)

        if not result.data.success:
            return Result.fail(f"Command failed: {result.data.stderr}")

        return Result.ok(result.data.stdout)

    def get_source_name(self) -> str:
        return self._source_name


class CollectionWorker(Component, Subject):
    """Independent collection worker with threading."""

    def __init__(self, collector: DataCollector[T], interval: float = 1.0, max_samples: int = 1000):
        super().__init__(f"Worker-{collector.get_source_name()}")
        self._collector = collector
        self._interval = interval
        self._max_samples = max_samples

        self._samples: queue.Queue[Sample[T]] = queue.Queue(maxsize=max_samples)
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

        # Statistics
        self._total_collected = 0
        self._failed_collections = 0
        self._last_collection_time: datetime | None = None

    def _do_initialize(self) -> None:
        """Initialize collection worker."""

    def _do_cleanup(self) -> None:
        """Cleanup collection worker."""
        self.stop()

    def start(self) -> Result[None]:
        """Start collection worker."""
        if self._running:
            return Result.ok(None)

        try:
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._collection_loop, daemon=True, name=f"collector-{self._collector.get_source_name()}"
            )
            self._worker_thread.start()
            self._running = True

            self._logger.info(f"Started collection worker for {self._collector.get_source_name()}")
            return Result.ok(None)

        except Exception as e:
            self._logger.exception("Failed to start collection worker")
            return Result.fail(str(e))

    def stop(self) -> None:
        """Stop collection worker."""
        if not self._running:
            return

        self._stop_event.set()

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)

        self._running = False
        self._logger.info(f"Stopped collection worker for {self._collector.get_source_name()}")

    def get_samples(self, max_count: int | None = None) -> list[Sample[T]]:
        """Get collected samples."""
        samples = []
        count = 0

        while not self._samples.empty() and (max_count is None or count < max_count):
            try:
                sample = self._samples.get_nowait()
                samples.append(sample)
                count += 1
            except queue.Empty:
                break

        return samples

    def get_latest_sample(self) -> Sample[T] | None:
        """Get most recent sample without removing from queue."""
        samples = self.get_samples(1)
        return samples[0] if samples else None

    def clear_samples(self) -> None:
        """Clear all collected samples."""
        while not self._samples.empty():
            try:
                self._samples.get_nowait()
            except queue.Empty:
                break

    def get_statistics(self) -> dict[str, Any]:
        """Get collection statistics."""
        return {
            "source": self._collector.get_source_name(),
            "running": self._running,
            "total_collected": self._total_collected,
            "failed_collections": self._failed_collections,
            "queue_size": self._samples.qsize(),
            "last_collection": self._last_collection_time.isoformat() if self._last_collection_time else None,
            "interval": self._interval,
        }

    def _collection_loop(self) -> None:
        """Main collection loop."""
        while not self._stop_event.is_set():
            try:
                start_time = time.time()

                # Collect data
                result = self._collector.collect()

                if result.success:
                    sample = Sample.create(
                        data=result.data,
                        source=self._collector.get_source_name(),
                        metadata={"collection_time": time.time() - start_time},
                    )

                    # Add to queue (remove oldest if full)
                    if self._samples.full():
                        with contextlib.suppress(queue.Empty):
                            self._samples.get_nowait()

                    self._samples.put(sample)
                    self._total_collected += 1
                    self._last_collection_time = sample.timestamp

                    # Notify observers
                    self.notify(sample)

                else:
                    self._failed_collections += 1
                    self._logger.warning(f"Collection failed: {result.error}")

                # Sleep for interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self._interval - elapsed)
                if sleep_time > 0:
                    self._stop_event.wait(sleep_time)

            except Exception:
                self._logger.exception("Collection loop error")
                self._failed_collections += 1
                self._stop_event.wait(1)  # Brief pause on error


class CollectionManager(Component):
    """Manages multiple collection workers."""

    def __init__(self):
        super().__init__("CollectionManager")
        self._workers: dict[str, CollectionWorker] = {}
        self._observers: list[Observer] = []

    def _do_initialize(self) -> None:
        """Initialize collection manager."""

    def _do_cleanup(self) -> None:
        """Cleanup collection manager."""
        self.stop_all()

    def add_collector(self, collector: DataCollector[T], interval: float = 1.0, max_samples: int = 1000) -> Result[str]:
        """Add data collector."""
        try:
            source_name = collector.get_source_name()

            if source_name in self._workers:
                return Result.fail(f"Collector {source_name} already exists")

            worker = CollectionWorker(collector, interval, max_samples)

            # Add observers to worker
            for observer in self._observers:
                worker.attach(observer)

            self._workers[source_name] = worker

            self._logger.info(f"Added collector: {source_name}")
            return Result.ok(source_name)

        except Exception as e:
            self._logger.exception("Failed to add collector")
            return Result.fail(str(e))

    def remove_collector(self, source_name: str) -> Result[None]:
        """Remove data collector."""
        if source_name not in self._workers:
            return Result.fail(f"Collector {source_name} not found")

        worker = self._workers[source_name]
        worker.stop()
        del self._workers[source_name]

        self._logger.info(f"Removed collector: {source_name}")
        return Result.ok(None)

    def start_collector(self, source_name: str) -> Result[None]:
        """Start specific collector."""
        if source_name not in self._workers:
            return Result.fail(f"Collector {source_name} not found")

        return self._workers[source_name].start()

    def stop_collector(self, source_name: str) -> Result[None]:
        """Stop specific collector."""
        if source_name not in self._workers:
            return Result.fail(f"Collector {source_name} not found")

        self._workers[source_name].stop()
        return Result.ok(None)

    def start_all(self) -> None:
        """Start all collectors."""
        for worker in self._workers.values():
            worker.start()

    def stop_all(self) -> None:
        """Stop all collectors."""
        for worker in self._workers.values():
            worker.stop()

    def get_samples(self, source_name: str, max_count: int | None = None) -> list[Sample]:
        """Get samples from specific collector."""
        if source_name not in self._workers:
            return []

        return self._workers[source_name].get_samples(max_count)

    def get_all_samples(self) -> dict[str, list[Sample]]:
        """Get samples from all collectors."""
        return {name: worker.get_samples() for name, worker in self._workers.items()}

    def get_statistics(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all collectors."""
        return {name: worker.get_statistics() for name, worker in self._workers.items()}

    def add_observer(self, observer: Observer) -> None:
        """Add observer to all workers."""
        self._observers.append(observer)
        for worker in self._workers.values():
            worker.attach(observer)

    def remove_observer(self, observer: Observer) -> None:
        """Remove observer from all workers."""
        if observer in self._observers:
            self._observers.remove(observer)

        for worker in self._workers.values():
            worker.detach(observer)
