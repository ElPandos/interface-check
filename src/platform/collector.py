from collections import defaultdict
from datetime import UTC, datetime as dt
import logging
from pathlib import Path
import queue
import threading
import time
from typing import Any

from pympler import asizeof

from src.core.json import Json
from src.enums.command import Type
from src.models.config import Config
from src.platform.commands import Command
from src.tools.ethtool import EthtoolTool
from src.core.connect import SshConnection

logger = logging.getLogger(__name__)


class Sample:
    _start: dt = None
    _stop: dt = None

    _interface: str
    _config: Config
    _ssh_connection: SshConnection

    snapshot: Any = None

    def __init__(self, interface: str, config: Config, ssh_connection: SshConnection) -> None:
        self._interface = interface
        self._config = config
        self._ssh_connection = ssh_connection

    @property
    def start(self) -> dt:
        return self._start

    @property
    def stop(self) -> dt:
        return self._stop

    def collect(self, cmd: Command) -> Any:
        self._start = dt.now(tz=UTC)

        match cmd.command_type:
            case Type.MODIFY, Type.SYSTEM, Type.COMMON:
                pass  # Not implemented
            case Type.ETHTOOL:
                self.snapshot = EthtoolTool(self._interface, self._config, self._ssh_connection).parse_output(cmd)
            case Type.MLXLINK:
                pass  # Not implemented
            case Type.MLXCONFIG:
                pass  # Not implemented
            case Type.MST:
                pass  # Not implemented
            case _:
                pass  # Unknown command
        self._stop = dt.now(tz=UTC)

        return self


class PlotSampleData:
    _x_value: dt = None

    _y_value: float = None
    _y_axis_label: str = "Empty"

    def __init__(self, sample: Sample, source: str, value: str) -> None:
        snap = sample.snapshot[source]
        snap_value = snap[value]

        # If the data contains xxx / yyy then it gets split up e.g. Celsuius and / Farenheit
        snap_value_first = snap_value
        if type(snap_value) is list and len(snap_value) > 1:
            snap_value_first = snap_value[0]

        # Get y axis label
        if type(snap_value_first.value) is int:
            self._y_axis_label = "Number"
        else:
            self._y_axis_label = snap_value_first.unit

        self._x_value = sample.begin
        self._y_value = snap_value_first.value

    @property
    def x(self) -> dt:
        return self._x_value

    @property
    def y(self) -> float:
        return self._y_value

    @property
    def y_label(self) -> str:
        return self._y_axis_label


class Worker(threading.Thread):
    _MAX_RECONNECT = 10

    _start: dt = None
    _stop: dt = None

    _interface: str
    _config: Config
    _ssh_connection: SshConnection

    _collected_samples: queue.Queue = queue.Queue()  # Thread safe queue
    _extracted_samples: list[Sample]

    def __init__(
        self, cmd: Command, interface: str, config: Config, ssh_connection: SshConnection, name: str = "Worker"
    ) -> None:
        super().__init__(name=name, daemon=True)  # daemon=True means it won’t block program exit
        self._cmd = cmd
        self._stop_event = threading.Event()
        self._extracted_samples = [Sample]

        self._interface = interface
        self._config = config
        self._ssh_connection = ssh_connection

    def run(self) -> None:
        """Thread main logic (executed when start() is called)."""
        self._start = dt.now(tz=UTC)

        reconnect = 1
        while not self._stop_event.is_set():
            try:
                if reconnect > self._MAX_RECONNECT:
                    logger.info("Reconnect failed 10 times. Exiting thread...")
                    reconnect = 0
                    break
                sample = Sample(self._interface, self._config, self._ssh_connection).collect(self._cmd)
                self._collected_samples.put(sample)
                time.sleep(self._config.gui.get_command_update_value())
            except KeyboardInterrupt:
                logger.info("User pressed 'Ctrl+c' - Exiting worker thread")
            except Exception:
                logger.exception("Collection stopped unexpectedly")
                try:
                    self._ssh_connection.connect()
                    if self._ssh_connection.is_connected():
                        logger.info("Reconnected to SSH session")
                    else:
                        logger.exception(f"Failed to reconnect to SSH session ({reconnect}/{self._MAX_RECONNECT})")
                except Exception:
                    logger.exception("SSH reconnect failed")
            reconnect += 1

        self._stop = dt.now(tz=UTC)

    def close(self) -> None:
        self._stop_event.set()
        logger.debug("Stop event set")

    def close_and_wait(self) -> None:
        self._stop_event.set()
        while self.is_alive():
            time.sleep(0.1)

    def is_closed(self) -> bool:
        """Return True if stop signal is active."""
        return self._stop_event.is_set()

    @property
    def interface(self) -> str:
        return self._interface

    @property
    def start(self) -> dt:
        return self._start

    @property
    def stop(self) -> dt:
        return self._stop

    @property
    def duration(self) -> str:
        if not self._start:
            return "Begin time not available"
        if not self._stop:
            return "End time not available"
        duration = self._stop - self._start
        return str(duration)

    def add(self, sample: Sample) -> None:
        self.collected_samples.put(sample)

    def clear(self) -> None:
        self._extracted_samples.clear()
        logger.debug("Clearing extracted samples")

    def log_extracted_size(self):
        logger.debug(f"Extracted list size: {len(self._extracted_samples)}")
        logger.debug(
            f"Mem size of extracted list: {round(asizeof.asizeof(self._extracted_samples) / (1024 * 1024), 2)} Mb"
        )

    def all_samples(self) -> list[Sample]:
        self._collect_all_samples()
        self.log_extracted_size()
        return self._extracted_samples

    def first_sample(self) -> Sample:
        if not self._extracted_samples:
            self._collect_sample()
        self.log_extracted_size()
        return self._extracted_samples[0]

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
        return [s for s in self.collected_samples.get() if hasattr(s, "begin") and start <= s.begin <= end]

    def group_by_type(self) -> dict:
        """Group samples by their concrete class name."""
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
    _work_pool: list[Worker]

    def __init__(self) -> None:
        self._work_pool = []

    def add(self, worker: Worker) -> None:
        old_worker = self.get_worker(worker.interface)
        if old_worker is None:
            worker.start()
            self._work_pool.append(worker)
        else:
            old_worker.start()
            logger.debug(f"Worker already exists for: {old_worker.interface}")

    def clear(self) -> None:
        logger.debug(f"Clearing {len(self._work_pool)} workers from pool")
        self._work_pool.clear()
        logger.debug("Work pool cleared")

    def stop_all(self) -> None:
        logger.debug(f"Stop all workers in pool: {len(self._work_pool)}")
        for w in self._work_pool:
            w.stop()
            logger.debug("Thread stopped")
            w.join()
            logger.debug("Thread joined")

    def reset(self) -> None:
        logger.debug("Reset work manager")
        self.stop_all()
        self.clear()
        logger.debug("Work manager has been resetted")

    def get_worker(self, interface: str) -> Worker | None:
        for w in self._work_pool:
            if w.interface == interface:
                logger.debug(f"Found worker: {w.interface}")
                return w
        logger.debug(f"Did not find any old worker for interface: {interface}")
        return None

    def summary(self) -> str:
        """One-line textual summary of the work pool."""
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
