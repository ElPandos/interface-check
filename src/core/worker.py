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
from src.core.enums.messages import LogMsg
from src.core.helpers import get_attr_value
from src.core.json import Json
from src.core.log.rotation import check_and_rotate_log
from src.core.parser import SutTimeParser
from src.core.sample import Sample
from src.core.statistics import WorkerStatistics
from src.interfaces.component import ITime
from src.models.config import Config
from src.platform.enums.log import LogName


class WorkerConfig:
    """Configuration for worker execution.

    Attributes:
        command: Shell command to execute
        pre_command: Optional command to execute once before loop starts
        parser: Optional parser class to process command output
        attributes: List of attribute names to extract from parsed results
        logger: Logger for worker
        scan_interval_ms: Polling interval in milliseconds
        max_log_size_kb: Maximum log file size in KB before rotation (default 102400KB = 100MB)
        is_flap_logger: Whether this logger tracks link flaps
        skip_header: Skip writing header row (data includes its own header)
        use_shell: Use interactive shell instead of exec_cmd (for SLX)
    """

    command: str = None
    pre_command: str | None = None
    parser: Any = None
    attributes: list[str] = None
    scan_interval_ms: int = 500
    max_log_size_kb: int = 102400
    is_flap_logger: bool = False
    skip_header: bool = False
    use_shell: bool = False


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
        shared_flap_state: dict | None = None,
        statistics: WorkerStatistics | None = None,
    ) -> None:
        """Initialize worker thread.

        Args:
            worker_cfg: Command configuration to execute
            cfg: Application configuration
            ssh: SSH connection for command execution
            shared_flap_state: Shared dictionary for flap detection across workers
            statistics: Shared statistics tracker for command durations
        """
        Thread.__init__(self, daemon=True)  # daemon=True prevents blocking app exit
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
        # Use shared dicts for rotation state (modified by rotation function)
        self._log_rotation_count_dict = {self._logger.name: 0}
        self._has_rotated_since_flap_dict = {self._logger.name: False}

    @property
    def _time_cmd_enabled(self) -> bool:
        """Check if time command parsing is enabled.

        Returns:
            True if time_cmd is enabled
        """
        return hasattr(self._cfg, "sut_time_cmd") and self._cfg.sut_time_cmd

    def _build_csv_header(self) -> str:
        """Build CSV header from worker config.

        Returns:
            CSV header string
        """
        headers = ["begin_timestamp"]
        if self._time_cmd_enabled:
            headers.append("time_cmd_ms")
        if self._worker_cfg.attributes:
            headers.extend(self._worker_cfg.attributes)
        else:
            headers.append("value")
        return ",".join(headers)

    def _extract_timing_data(self, sample: Sample) -> tuple[float, float, float]:
        """Extract timing data from sample command result.

        Args:
            sample: Sample with command result

        Returns:
            Tuple of (send_ms, read_ms, parsed_ms)
        """
        send_ms = 0.0
        read_ms = 0.0
        parsed_ms = 0.0

        if sample.cmd_result:
            send_ms = sample.cmd_result.send_ms
            read_ms = sample.cmd_result.read_ms
            parsed_ms = sample.cmd_result.parsed_ms

            if self._time_cmd_enabled:
                time_parser = SutTimeParser(self._logger.name)
                time_parser.parse(sample.cmd_result.stderr)
                parsed_ms = time_parser.get_result()

        return send_ms, read_ms, parsed_ms

    def _record_statistics(
        self,
        cmd_duration_ms: float,
        send_ms: float,
        read_ms: float,
        parsed_ms: float,
        cmd_start: float,
    ) -> None:
        """Record command duration statistics.

        Args:
            cmd_duration_ms: Total command duration
            send_ms: Send time
            read_ms: Read time
            parsed_ms: Parse time
            cmd_start: Command start timestamp
        """
        if hasattr(self, "_statistics") and self._statistics:
            cycle_ms = cmd_duration_ms + self._worker_cfg.scan_interval_ms
            self._statistics.record_duration(
                self._worker_cfg.command,
                cmd_duration_ms,
                send_ms=send_ms,
                read_ms=read_ms,
                cycle_ms=cycle_ms,
                parsed_ms=parsed_ms,
                timestamp=cmd_start,
            )

    def _parse_sample_output(self, sample: Sample) -> None:
        """Parse sample output using configured parser.

        Args:
            sample: Sample to parse (modified in place)
        """
        if self._worker_cfg.parser is not None:
            if hasattr(self._worker_cfg.parser, "_logger"):
                self._worker_cfg.parser._logger = self._logger  # noqa: SLF001
            self._worker_cfg.parser.parse(sample.snapshot)
            sample.snapshot = self._worker_cfg.parser.get_result()
        elif sample.snapshot is not None:
            sample.snapshot = sample.snapshot.strip()
        else:
            sample.snapshot = ""

    def _log_flap_data(self, timestamp: str, parsed_ms: float, flap: Any) -> None:
        """Log flap detection data.

        Args:
            timestamp: Begin timestamp
            parsed_ms: Parsed time in milliseconds
            flap: Flap object with interface, down_time, up_time, duration
        """
        self._shared_flap_state["flaps_detected"] = True
        self._shared_flap_state["last_flap_time"] = time.time()

        row = [timestamp]
        if self._time_cmd_enabled:
            row.append(f"{parsed_ms:.3f}")
        row.append(flap.interface)
        row.append(flap.down_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        row.append(flap.up_time.strftime("%Y-%m-%d %H:%M:%S.%f"))
        row.append(str(flap.duration))
        self._logger.info(",".join(row))

    def _log_sample_data(self, timestamp: str, parsed_ms: float, sample: Sample) -> None:
        """Log regular sample data.

        Args:
            timestamp: Begin timestamp
            parsed_ms: Parsed time in milliseconds
            sample: Sample with snapshot data
        """
        row = [timestamp]
        if self._time_cmd_enabled:
            row.append(f"{parsed_ms:.3f}")
        if self._worker_cfg.attributes is not None:
            row.extend(
                get_attr_value(sample.snapshot, attr) for attr in self._worker_cfg.attributes
            )
        else:
            row.append(sample.snapshot)
        self._logger.info(",".join(row))

    def run(self) -> None:
        """Main thread execution loop.

        Executes commands at configured intervals, parses output, logs data,
        and handles reconnection on failures. Runs until stop event is set.
        """
        self.start_timer()

        # Execute pre_command once before loop starts
        if self._worker_cfg.pre_command:
            try:
                self._ssh.exec_cmd(self._worker_cfg.pre_command)
            except Exception:
                self._logger.exception("Pre-command execution failed")

        # Write header unless skip_header is True
        if not self._worker_cfg.skip_header:
            self._write_raw_csv(self._build_csv_header())

        reconnect = 0
        while not self._stop_event.is_set():
            try:
                # Check reconnection limit
                if reconnect > self.MAX_RECONNECT:
                    self._logger.info(
                        f"{LogMsg.WORKER_RECONNECT_FAIL.value} {self.MAX_RECONNECT} times. Exiting worker thread: {self.name}"
                    )
                    break

                # Collect sample by executing command
                cmd_start = time.time()
                sample = Sample(self._cfg, self._ssh).collect(self._worker_cfg, logger=self._logger)
                cmd_duration_ms = (time.time() - cmd_start) * 1000

                # Skip interrupted samples (Ctrl+C during collection)
                if self._stop_event.is_set():
                    break

                # Extract timing data and record statistics
                send_ms, read_ms, parsed_ms = self._extract_timing_data(sample)
                self._record_statistics(cmd_duration_ms, send_ms, read_ms, parsed_ms, cmd_start)

                # Parse output
                self._parse_sample_output(sample)

                # Add to thread-safe queue
                self._collected_samples.put(sample)

                # Log sample value
                timestamp = (
                    sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if sample.begin else ""
                )

                # Skip logging if parser returned None (no change detected)
                if sample.snapshot is None:
                    reconnect = 0
                    sleep_time_ms = self._worker_cfg.scan_interval_ms
                    time.sleep(float(sleep_time_ms / 1000))
                    continue

                # Log data
                if hasattr(sample.snapshot, "flaps"):
                    for flap in sample.snapshot.flaps:
                        self._log_flap_data(timestamp, parsed_ms, flap)
                else:
                    self._log_sample_data(timestamp, parsed_ms, sample)

                # Check log size and rotate if needed
                self._check_and_rotate_log()

                reconnect = 0  # Reset counter on success
                sleep_time_ms = self._worker_cfg.scan_interval_ms
                time.sleep(float(sleep_time_ms / 1000))

            except KeyboardInterrupt:
                self._logger.info(f"{LogMsg.WORKER_USER_EXIT.value}: {self.name}")
                break
            except Exception as e:
                self._logger.exception(f"{LogMsg.WORKER_STOPPED.value}: {type(e).__name__}: {e}")
                reconnect += 1
                # Don't attempt reconnection - SSH connection is shared and managed externally
                self._logger.error(
                    f"Worker error - Attempt {reconnect}/{self.MAX_RECONNECT} - Command: {self._worker_cfg.command}"
                )
                if reconnect >= self.MAX_RECONNECT:
                    self._logger.critical(
                        f"Worker {self.name} exceeded max reconnect attempts. Thread will exit."
                    )
                time.sleep(min(reconnect, 5))  # Exponential backoff up to 5s

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
        self._logger.debug(LogMsg.WORKER_CLEAR_SAMPLES.value)

    def _write_raw_csv(self, line: str) -> None:
        """Write raw CSV line directly to log file without logging prefix.

        Args:
            line: CSV line to write
        """
        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler):
                try:
                    with Path(handler.baseFilename).open("a") as f:
                        f.write(line + "\n")
                except Exception:
                    self._logger.exception("Failed to write raw CSV")
                break

    def _check_and_rotate_log(self) -> None:
        """Check log file size and rotate if needed."""
        # Flap logger: never rotate or clear, just keep growing
        if self._worker_cfg.is_flap_logger:
            return

        # Use common rotation logic with CSV header preservation
        check_and_rotate_log(
            self._logger,
            self._worker_cfg.max_log_size_kb,
            self._shared_flap_state,
            self._has_rotated_since_flap_dict,
            self._log_rotation_count_dict,
            keep_header=True,
            csv_header=self._build_csv_header(),
            timeout_sec=self._cfg.log_rotation_timeout_sec,
        )

    def _log_mem_size(self, collection: Any) -> None:
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
        """Get first sample from queue.

        Returns:
            First sample or None if queue is empty
        """
        if not self._extracted_samples:
            self._collect_samples()
            self._log_mem_size(self._extracted_samples[0])
            return self._extracted_samples[0]
        return None

    def _collect_samples(self) -> None:
        """Collect single sample from queue and add to extracted samples."""
        self._extracted_samples.append(self._collected_samples.get())

    def _collect_all_samples(self) -> None:
        """Collect all available samples from queue and add to extracted samples."""
        while True:
            try:
                self._extracted_samples.append(self._collected_samples.get_nowait())
            except queue.Empty:
                break

    def get_range(self, start: dt, end: dt) -> list[Sample]:
        """Get samples within specified time range.

        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)

        Returns:
            List of samples within time range
        """
        return [
            s
            for s in self.collected_samples.get()
            if hasattr(s, "begin") and start <= s.begin <= end
        ]

    def group_by_type(self) -> dict[str, list[Sample]]:
        """Group samples by their class name.

        Returns:
            Dictionary mapping class names to lists of samples
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
        """Generate one-line summary of collected sample data.

        Returns:
            Summary string with sample count and types
        """
        total_samples = len(self._collected_samples)
        types = {type(s).__name__ for s in self._collected_samples.get()}
        return f"Collected {total_samples} samples of types: {', '.join(sorted(types))}"


class WorkManager:
    """Manages a pool of worker threads.

    Provides centralized management for multiple worker threads including
    lifecycle management, statistics tracking, and shared state coordination.
    """

    def __init__(self) -> None:
        """Initialize empty worker pool."""
        self._work_pool: list[Worker] = []
        self._shared_flap_state = {"flaps_detected": False, "workers_rotated": set()}
        self._statistics = WorkerStatistics()

        self._logger = logging.getLogger(LogName.MAIN.value)

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
            self._logger.debug(f"{LogMsg.WORKER_ALREADY_EXISTS.value}: {worker.command}")

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
        self._logger.debug(
            f"{LogMsg.WORKER_POOL_CLEAR.value} {len(self._work_pool)} workers from pool"
        )
        self._work_pool.clear()
        self._logger.debug(LogMsg.WORKER_POOL_CLEARED.value)

    def stop_all(self) -> None:
        """Stop all workers in pool and wait for completion."""
        self._logger.debug(
            f"{LogMsg.WORKER_POOL_STOP.value} {len(self._work_pool)} workers in pool"
        )
        for w in self._work_pool:
            w.close_and_wait()
            self._logger.debug(f"{LogMsg.WORKER_STOPPED_NAME.value} '{w.name}'")
            w.join()
            self._logger.debug(f"{LogMsg.WORKER_JOINED_NAME.value} '{w.name}'")

    def reset(self) -> None:
        """Reset work manager."""
        self._logger.debug(LogMsg.WORKER_RESET.value)
        self.stop_all()
        self.clear()
        self._logger.debug(LogMsg.WORKER_RESET_DONE.value)

    def get_worker(self, command: str) -> Worker | None:
        """Get worker by command string.

        Args:
            command: Command string to search for

        Returns:
            Worker instance if found, None otherwise
        """
        for w in self._work_pool:
            if w.command == command:
                self._logger.debug(f"{LogMsg.WORKER_FOUND.value}: {w.command}")
                return w
        self._logger.debug(f"{LogMsg.WORKER_NOT_FOUND.value}: {command}")
        return None

    def get_workers_in_pool(self) -> list[Worker]:
        """Get all workers in pool.

        Returns:
            List of workers
        """
        return self._work_pool

    def summary(self) -> str:
        """Generate one-line summary of worker pool.

        Returns:
            Summary string with worker count and types
        """
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
