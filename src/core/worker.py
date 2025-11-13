"""Worker thread management for background data collection.

This module provides:
- Worker: Background thread for executing commands and collecting samples
- WorkManager: Pool manager for multiple worker threads
- WorkerCommand: Command configuration with optional parser
"""

from collections import defaultdict
from datetime import datetime as dt
import logging
from pathlib import Path
import queue
from threading import Event, Thread
import time
from typing import Any

from pympler import asizeof

from src.core.connect import SshConnection
from src.core.helpers import get_attr_value
from src.core.json import Json
from src.core.sample import Sample
from src.interfaces.component import ITime
from src.models.config import Config
from src.platform.enums.log import LogName


class WorkerConfig:
    """Configuration for worker execution.

    Attributes:
        command: Shell command to execute
        parser: Optional parser class to process command output
        logger: Logger for worker
    """

    command: str = None
    parser: Any = None
    attrs: list[str] = None
    logger: logging.Logger = None
    mem_logger: logging.Logger = None


class Worker(Thread, ITime):
    """Background worker thread for periodic command execution.

    Executes commands at configured intervals, collects output samples,
    and handles automatic reconnection on failures.

    Attributes:
        MAX_RECONNECT: Maximum reconnection attempts before giving up
    """

    def __init__(
        self,
        worker_config: WorkerConfig,
        cfg: Config,
        ssh: SshConnection,
        name: str = "Worker",
    ) -> None:
        """Initialize worker thread.

        Args:
            worker_command: Command configuration to execute
            config: Application configuration
            ssh: SSH connection for command execution
            name: Thread name for identification
        """
        Thread.__init__(self, name=name, daemon=True)  # daemon=True prevents blocking app exit
        ITime.__init__(self)

        self.MAX_RECONNECT = 10

        self._worker_config = worker_config
        self._cfg = cfg
        self._ssh = ssh

        self._stop_event = Event()  # Signal for graceful shutdown

        self._collected_samples: queue.Queue = queue.Queue()  # Thread-safe queue for samples
        self._extracted_samples: list[Sample] = []  # Extracted samples for analysis

        self._logger = self._worker_config.logger

    def run(self) -> None:
        """Main thread execution loop."""
        self.start_timer()

        headers = [
            "begin_timestamp",
        ]
        if self._worker_config.attrs is not None:
            headers.extend(self._worker_config.attrs)
        else:
            headers.append("value")

        self._logger.info(",".join(headers))

        reconnect = 0
        while not self._stop_event.is_set():
            try:
                # Check reconnection limit
                if reconnect > self.MAX_RECONNECT:
                    self._logger.info(
                        f"Reconnect failed {self.MAX_RECONNECT} times. Exiting worker thread: {self.name}"
                    )
                    break

                # Collect sample by executing command
                sample = Sample(self._cfg, self._ssh).collect(self._worker_config)

                # Parse output if parser provided
                if self._worker_config.parser is not None:
                    sample.snapshot = self._worker_config.parser(sample.snapshot).get_result()
                elif sample.snapshot is not None:
                    sample.snapshot = sample.snapshot.strip()
                else:
                    sample.snapshot = ""

                # Add to thread-safe queue
                self._collected_samples.put(sample)

                # Log sample value
                row = []
                timestamp = (
                    sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if sample.begin else ""
                )
                row.append(timestamp)
                if self._worker_config.attrs is not None:
                    row.extend(
                        get_attr_value(sample.snapshot, attr) for attr in self._worker_config.attrs
                    )
                else:
                    row.append(sample.snapshot)
                self._logger.info(",".join(row))

                # Log collected mem usage, can t check size on queue
                # if self._worker_config.mem_logger is not None:
                #    self._log_mem_size(self._collected_samples)

                reconnect = 0  # Reset counter on success
                time.sleep(float(self._cfg.sut_scan_interval))

            except KeyboardInterrupt:
                self._logger.info(f"User pressed 'ctrl+c' - Exiting worker thread: {self.name}")
                break
            except Exception:
                self._logger.exception("Worker thread stopped unexpectedly")
                reconnect += 1

                # Attempt reconnection
                try:
                    if self._ssh.connect():
                        self._logger.info("Reconnect was established successfully")
                        reconnect = 0  # Reset on successful reconnect
                    else:
                        self._logger.exception(
                            f"Failed to reconnect to host ({reconnect}/{self.MAX_RECONNECT})"
                        )
                except Exception:
                    self._logger.exception("Failed to reconnect to host")

        self.stop_timer()

    def close(self) -> None:
        """Signal worker to stop execution."""
        self._stop_event.set()
        self._logger.debug("Stop event is set")

    def close_and_wait(self) -> None:
        """Stop worker and wait for thread to finish."""
        self.close()
        while self.is_alive():
            time.sleep(0.1)

    @property
    def command(self) -> str:
        """Get worker command.

        Returns:
            Command string
        """
        return self._worker_config.command

    def add(self, sample: Sample) -> None:
        """Add sample to queue.

        Args:
            sample: Sample to add
        """
        self.collected_samples.put(sample)

    def clear(self) -> None:
        """Clear extracted samples."""
        self._extracted_samples.clear()
        self._logger.debug("Clearing extracted samples")

    def _log_mem_size(self, collection: Any):
        """Log memory size of collection.

        Args:
            collection: Collection to measure
        """
        self._logger.debug(f"({__name__}) Extracted list size: {len(collection)}")
        self._logger.debug(
            f"Mem size of extracted list: {round(asizeof.asizeof(collection) / (1024 * 1024), 2)} Mb"
        )

    def get_extracted_samples(self) -> list[Sample]:
        """Get extracted samples.

        Returns:
            List of samples
        """
        return self._extracted_samples

    def extract_all_samples(self) -> None:
        """Extract all samples from queue."""
        self._collect_all_samples()
        self._log_mem_size(self._extracted_samples)

    def first_sample(self) -> Sample | None:
        """Get first sample.

        Returns:
            First sample or None
        """
        if not self._extracted_samples:
            self._collect_samples()
            self._log_mem_size(self._extracted_samples[0])
            return self._extracted_samples[0]
        return None

    def _collect_samples(self) -> None:
        """Collect samples from queue."""
        self._extracted_samples.append(self._collected_samples.get())

    def _collect_all_samples(self) -> None:
        """Collect all samples from queue."""
        while True:
            try:
                self._extracted_samples.append(self._collected_samples.get_nowait())
            except queue.Empty:
                break

    def get_range(self, start: dt, end: dt) -> list[Sample]:
        """Get samples in time range.

        Args:
            start: Start time
            end: End time

        Returns:
            List of samples
        """
        return [
            s
            for s in self.collected_samples.get()
            if hasattr(s, "begin") and start <= s.begin <= end
        ]

    def group_by_type(self) -> dict:
        """Group samples by their class name.

        Returns:
            Dictionary of grouped samples
        """
        groups = defaultdict(list)
        for s in self.collected_samples.get():
            groups[type(s).__name__].append(s)
        return dict(groups)

    def export_json(self, full_path: Path) -> None:
        """Export samples to JSON.

        Args:
            full_path: Output file path
        """
        Json.save(self.get_samples(), full_path)

    def summary(self) -> str:
        """One-line textual summary of the collected sample data.

        Returns:
            Summary string
        """
        total_samples = len(self._collected_samples)
        types = {type(s).__name__ for s in self._collected_samples.get()}
        return f"Collected {total_samples} samples of types: {', '.join(sorted(types))}"


class WorkManager:
    """Manages a pool of worker threads."""

    def __init__(self) -> None:
        """Initialize empty worker pool."""
        self._work_pool: list[Worker] = []

        self._logger = logging.getLogger(LogName.CORE_MAIN.value)

    def add(self, worker: Worker) -> None:
        """Add worker to pool and start execution.

        Args:
            worker: Worker instance to add
        """
        old_worker = self.get_worker(worker.command)
        if old_worker is None:
            worker.start()
            self._work_pool.append(worker)
        else:
            old_worker.start()
            self._logger.debug(f"Worker already exists for command: {worker.command}")

    def clear(self) -> None:
        """Clear worker pool."""
        self._logger.debug(f"Clearing {len(self._work_pool)} workers from pool")
        self._work_pool.clear()
        self._logger.debug("Work pool cleared")

    def stop_all(self) -> None:
        """Stop all workers in pool and wait for completion."""
        self._logger.debug(f"Stopping all {len(self._work_pool)} workers in pool")
        for w in self._work_pool:
            w.close_and_wait()
            self._logger.debug(f"Worker '{w.name}' stopped")
            w.join()
            self._logger.debug(f"Worker '{w.name}' joined")

    def reset(self) -> None:
        """Reset work manager."""
        self._logger.debug("Reset work manager")
        self.stop_all()
        self.clear()
        self._logger.debug("Work manager has been resetted")

    def get_worker(self, command: str) -> Worker | None:
        """Get worker by command.

        Args:
            command: Command string

        Returns:
            Worker or None
        """
        for w in self._work_pool:
            if w.command == command:
                self._logger.debug(f"Found worker: {w.command}")
                return w
        self._logger.debug(f"Did not find any old worker for interface: {command}")
        return None

    def get_workers_in_pool(self) -> list[Worker]:
        """Get all workers in pool.

        Returns:
            List of workers
        """
        return self._work_pool

    def summary(self) -> str:
        """One-line textual summary of the work pool.

        Returns:
            Summary string
        """
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
