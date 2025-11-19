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
from src.core.statistics import WorkerStatistics
from src.interfaces.component import ITime
from src.models.config import Config
from src.platform.enums.log import LogName


class WorkerConfig:
    """Configuration for worker execution.

    Attributes:
        command: Shell command to execute
        parser: Optional parser class to process command output
        logger: Logger for worker
        scan_interval_ms: Polling interval in milliseconds
        max_log_size_kb: Maximum log file size in KB before rotation (default 102400KB = 100MB)
        is_flap_logger: Whether this logger tracks link flaps
    """

    command: str = None
    parser: Any = None
    attributes: list[str] = None
    scan_interval_ms: int = 500
    max_log_size_kb: int = 102400
    is_flap_logger: bool = False


class Worker(Thread, ITime):
    """Background worker thread for periodic command execution.

    Executes commands at configured intervals, collects output samples,
    and handles automatic reconnection on failures.

    Attributes:
        MAX_RECONNECT: Maximum reconnection attempts before giving up
    """

    def __init__(
        self,
        worker_cfg: WorkerConfig,
        cfg: Config,
        ssh: SshConnection,
        name: str = "Worker",
        shared_flap_state: dict | None = None,
        statistics: WorkerStatistics | None = None,
    ) -> None:
        """Initialize worker thread.

        Args:
            worker_command: Command configuration to execute
            config: Application configuration
            ssh: SSH connection for command execution
            name: Thread name for identification
            shared_flap_state: Shared dictionary for flap detection across workers
            statistics: Shared statistics tracker for command durations
        """
        Thread.__init__(self, name=name, daemon=True)  # daemon=True prevents blocking app exit
        ITime.__init__(self)

        self.MAX_RECONNECT = 10

        self._worker_cfg = worker_cfg
        self._cfg = cfg
        self._ssh = ssh
        self._shared_flap_state = shared_flap_state or {
            "flaps_detected": False,
            "workers_rotated": set(),
        }
        self._worker_id = id(self)  # Unique worker identifier
        self._statistics = statistics

        self._stop_event = Event()  # Signal for graceful shutdown

        self._collected_samples: queue.Queue = queue.Queue()  # Thread-safe queue for samples
        self._extracted_samples: list[Sample] = []  # Extracted samples for analysis

        self._logger = worker_cfg.logger
        self._log_rotation_count = 0  # Track number of log rotations
        self._has_rotated_since_flap = False  # Track if this worker rotated since last flap

    def run(self) -> None:
        """Main thread execution loop."""
        self.start_timer()

        headers = [
            "begin_timestamp",
        ]
        if self._worker_cfg.attributes is not None:
            headers.extend(self._worker_cfg.attributes)
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
                cmd_start = time.time()
                sample = Sample(self._cfg, self._ssh).collect(self._worker_cfg)
                cmd_duration_ms = (time.time() - cmd_start) * 1000
                self._logger.debug(f"Command execution took: {cmd_duration_ms:.1f} ms")
                
                # Record duration in statistics (if statistics object provided)
                if hasattr(self, '_statistics') and self._statistics:
                    self._statistics.record_duration(self._worker_cfg.command, cmd_duration_ms)

                # Parse output if parser provided
                if self._worker_cfg.parser is not None:
                    self._worker_cfg.parser.parse(sample.snapshot)
                    sample.snapshot = self._worker_cfg.parser.get_result()
                elif sample.snapshot is not None:
                    sample.snapshot = sample.snapshot.strip()
                else:
                    sample.snapshot = ""

                # Add to thread-safe queue
                self._collected_samples.put(sample)

                # Log sample value
                timestamp = (
                    sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if sample.begin else ""
                )

                # Special handling for DmesgFlapResult - log each flap on separate row
                if hasattr(sample.snapshot, "flaps"):
                    for flap in sample.snapshot.flaps:
                        self._shared_flap_state["flaps_detected"] = True  # Mark that flaps occurred
                        row = [timestamp]
                        row.append(flap.interface)
                        row.append(flap.down_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
                        row.append(flap.up_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
                        row.append(str(flap.duration))
                        self._logger.info(",".join(row))
                else:
                    row = [timestamp]
                    if self._worker_cfg.attributes is not None:
                        row.extend(
                            get_attr_value(sample.snapshot, attr)
                            for attr in self._worker_cfg.attributes
                        )
                    else:
                        row.append(sample.snapshot)
                    self._logger.info(",".join(row))

                # Check log size and rotate if needed
                self._check_and_rotate_log()

                # Log collected mem usage, can t check size on queue
                # if self._worker_config.mem_logger is not None:
                #    self._log_mem_size(self._collected_samples)

                reconnect = 0  # Reset counter on success
                sleep_time_ms = self._worker_cfg.scan_interval_ms
                total_cycle_ms = cmd_duration_ms + sleep_time_ms
                self._logger.debug(
                    f"Sleeping {sleep_time_ms} ms (Total cycle: {total_cycle_ms:.1f} ms)"
                )
                time.sleep(float(sleep_time_ms / 1000))

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
        return self._worker_cfg.command

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

    def _check_and_rotate_log(self) -> None:
        """Check log file size and rotate if needed."""
        # Get log file path from logger handlers
        log_file = None
        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                log_file = Path(handler.baseFilename)
                break

        if not log_file or not log_file.exists():
            return

        # Check file size
        file_size_kb = log_file.stat().st_size / 1024
        if file_size_kb < self._worker_cfg.max_log_size_kb:
            return

        # Log size exceeded
        if self._worker_cfg.is_flap_logger:
            # Flap logger: never rotate or clear, just keep growing
            return
        # Other loggers: rotate with suffix if flaps detected, otherwise clear
        if self._shared_flap_state.get("flaps_detected", False):
            if self._has_rotated_since_flap:
                # Already rotated once since flap, now clear and reset flag
                self._clear_log_keep_header(log_file)
                self._shared_flap_state["flaps_detected"] = False
                self._has_rotated_since_flap = False
                self._logger.debug("Cleared log and reset flap flag after one rotation cycle")
            else:
                # First rotation since flap detected
                self._rotate_to_new_file(log_file)
                self._has_rotated_since_flap = True
        else:
            self._clear_log_keep_header(log_file)
            self._has_rotated_since_flap = False

    def _rotate_to_new_file(self, log_file: Path) -> None:
        """Rotate to new log file with suffix.

        Args:
            log_file: Current log file path
        """
        self._log_rotation_count += 1
        # Extract base name without previous rotation suffix
        base_stem = (
            log_file.stem.rsplit("_", 1)[0]
            if "_" in log_file.stem and log_file.stem.split("_")[-1].isdigit()
            else log_file.stem
        )
        new_log_file = log_file.with_name(
            f"{base_stem}_{self._log_rotation_count}{log_file.suffix}"
        )

        # Close current handler
        for handler in self._logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self._logger.removeHandler(handler)

        # Create new handler with new file
        new_handler = logging.FileHandler(new_log_file)
        new_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)-30s - %(levelname)-8s - %(message)s")
        )
        new_handler.setLevel(self._logger.level)
        self._logger.addHandler(new_handler)

        # Log header in new file
        headers = ["begin_timestamp"]
        if self._worker_cfg.attributes:
            headers.extend(self._worker_cfg.attributes)
        else:
            headers.append("value")
        self._logger.info(",".join(headers))

    def _clear_log_keep_header(self, log_file: Path) -> None:
        """Clear log file but keep header row.

        Args:
            log_file: Log file path to clear
        """
        # Read first line (header)
        header = None
        try:
            with log_file.open("r") as f:
                for line in f:
                    if "begin_timestamp" in line:
                        header = line
                        break
        except Exception:
            self._logger.exception("Failed to read header from log file")
            return

        if not header:
            return

        # Close current handler
        for handler in self._logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self._logger.removeHandler(handler)

        # Truncate file and write header
        try:
            with log_file.open("w") as f:
                f.write(header)
        except Exception:
            self._logger.exception("Failed to clear log file")

        # Reopen handler
        new_handler = logging.FileHandler(log_file)
        new_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)-30s - %(levelname)-8s - %(message)s")
        )
        new_handler.setLevel(self._logger.level)
        self._logger.addHandler(new_handler)

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
        self._shared_flap_state = {"flaps_detected": False, "workers_rotated": set()}
        self._statistics = WorkerStatistics()

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
    
    def get_statistics_summary(self) -> str:
        """Get statistics summary for all workers.
        
        Returns:
            Formatted statistics summary
        """
        return self._statistics.get_summary()
    
    def get_statistics(self) -> WorkerStatistics:
        """Get statistics object.
        
        Returns:
            WorkerStatistics instance
        """
        return self._statistics

    def get_shared_flap_state(self) -> dict:
        """Get shared flap detection state.

        Returns:
            Dictionary with flap detection state
        """
        return self._shared_flap_state

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
