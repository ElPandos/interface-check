from collections import defaultdict
from datetime import datetime as dt
import logging
from pathlib import Path
import queue
import threading
import time
from typing import Any

from pympler import asizeof

from src.core.connect import SshConnection
from src.core.json import Json
from src.core.sample import Sample
from src.models.config import Config
from src.platform.enums.log import LogName


class WorkerCommand:
    command: str = None
    parser: Any = None


class Worker(threading.Thread):
    _MAX_RECONNECT = 10

    def __init__(
        self,
        worker_command: WorkerCommand,
        config: Config,
        ssh_connection: SshConnection,
        name: str = "Worker",
    ) -> None:
        super().__init__(name=name, daemon=True)  # daemon=True means it won’t block program exit

        self._begin: dt = None
        self._end: dt = None

        self._worker_command = worker_command
        self._stop_event = threading.Event()

        self._collected_samples: queue.Queue = queue.Queue()  # Thread safe queue
        self._extracted_samples: list[Sample] = []

        self._config = config
        self._ssh_connection = ssh_connection

        self._logger = logging.getLogger(LogName.MAIN.value)

    def run(self) -> None:
        """Thread main logic (executed when start() is called)."""
        self._begin = dt.now(tz=dt.now().astimezone().tzinfo)

        reconnect = 0
        while not self._stop_event.is_set():
            try:
                if reconnect > self._MAX_RECONNECT:
                    self._logger.info("Reconnect failed 10 times. Exiting thread...")
                    break

                sample = Sample(self._config, self._ssh_connection).collect(self._worker_command)
                if self._worker_command.parser is not None:
                    sample.snapshot = self._worker_command.parser(sample.snapshot).result()
                elif sample.snapshot is not None:
                    sample.snapshot = sample.snapshot.strip()
                else:
                    sample.snapshot = None

                self._collected_samples.put(sample)
                reconnect = 0  # Reset on success
                time.sleep(float(self._config.sut_scan_interval))
            except KeyboardInterrupt:
                self._logger.info(f"User pressed 'Ctrl+c' - Exiting worker thread: {self.name}")
                break
            except Exception:
                self._logger.exception("Collection stopped unexpectedly")
                reconnect += 1
                try:
                    self._ssh_connection.connect()
                    if self._ssh_connection.is_connected():
                        self._logger.info("Reconnected to SSH session")
                        reconnect = 0  # Reset on successful reconnect
                    else:
                        self._logger.exception(
                            f"Failed to reconnect to SSH session ({reconnect}/{self._MAX_RECONNECT})"
                        )
                except Exception:
                    self._logger.exception("SSH reconnect failed")

        self._end = dt.now(tz=dt.now().astimezone().tzinfo)

    def close(self) -> None:
        self._stop_event.set()
        self._logger.debug("Stop event set")

    def close_and_wait(self) -> None:
        self._stop_event.set()
        while self.is_alive():
            time.sleep(0.1)

    def is_closed(self) -> bool:
        """Return True if stop signal is active."""
        return self._stop_event.is_set()

    @property
    def begin(self) -> dt:
        return self._begin

    @property
    def end(self) -> dt:
        return self._end

    @property
    def duration(self) -> str:
        if not self._begin:
            return "Begin time not available"
        if not self._end:
            return "End time not available"
        duration = self._end - self._begin
        return str(duration)

    @property
    def command(self) -> str:
        return self._worker_command.command

    def add(self, sample: Sample) -> None:
        self.collected_samples.put(sample)

    def clear(self) -> None:
        self._extracted_samples.clear()
        self._logger.debug("Clearing extracted samples")

    def _log_extracted_size(self):
        self._logger.debug(f"Extracted list size: {len(self._extracted_samples)}")
        self._logger.debug(
            f"Mem size of extracted list: {round(asizeof.asizeof(self._extracted_samples) / (1024 * 1024), 2)} Mb"
        )

    def get_extracted_samples(self) -> list[Sample]:
        return self._extracted_samples

    def extract_all_samples(self) -> None:
        self._collect_all_samples()
        self._log_extracted_size()

    def first_sample(self) -> Sample | None:
        if not self._extracted_samples:
            self._collect_sample()
            self._log_extracted_size()
            return self._extracted_samples[0]
        return None

    def _collect_sample(self) -> None:
        # Will lock main thread until first sample is received
        self._extracted_samples.append(self._collected_samples.get())

    def _collect_all_samples(self) -> None:
        while True:
            try:
                self._extracted_samples.append(self._collected_samples.get_nowait())
            except queue.Empty:
                break

    def get_range(self, start: dt, end: dt) -> list[Sample]:
        return [
            s
            for s in self.collected_samples.get()
            if hasattr(s, "begin") and start <= s.begin <= end
        ]

    def group_by_type(self) -> dict:
        """Group samples by their class name."""
        groups = defaultdict(list)
        for s in self.collected_samples.get():
            groups[type(s).__name__].append(s)
        return dict(groups)

    def export_json(self, full_path: Path) -> None:
        Json.save(self.get_samples(), full_path)

    def summary(self) -> str:
        """One-line textual summary of the collected sample data."""
        total_samples = len(self._collected_samples)
        types = {type(s).__name__ for s in self._collected_samples.get()}
        return f"Collected {total_samples} samples of types: {', '.join(sorted(types))}"


class WorkManager:
    def __init__(self) -> None:
        self._work_pool: list[Worker] = []

        self._logger = logging.getLogger(LogName.MAIN.value)

    def add(self, worker: Worker) -> None:
        old_worker = self.get_worker(worker.command)
        if old_worker is None:
            worker.start()
            self._work_pool.append(worker)
        else:
            old_worker.start()
            self._logger.debug(f"Worker already exists for: {old_worker.interface}")

    def clear(self) -> None:
        self._logger.debug(f"Clearing {len(self._work_pool)} workers from pool")
        self._work_pool.clear()
        self._logger.debug("Work pool cleared")

    def stop_all(self) -> None:
        self._logger.debug(f"Stop all workers in pool: {len(self._work_pool)}")
        for w in self._work_pool:
            w.close_and_wait()
            self._logger.debug("Thread stopped")
            w.join()
            self._logger.debug("Thread joined")

    def reset(self) -> None:
        self._logger.debug("Reset work manager")
        self.stop_all()
        self.clear()
        self._logger.debug("Work manager has been resetted")

    def get_worker(self, command: str) -> Worker | None:
        for w in self._work_pool:
            if w.command == command:
                self._logger.debug(f"Found worker: {w.command}")
                return w
        self._logger.debug(f"Did not find any old worker for interface: {command}")
        return None

    def get_workers_in_pool(self) -> list[Worker]:
        return self._work_pool

    def summary(self) -> str:
        """One-line textual summary of the work pool."""
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
