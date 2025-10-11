from ast import parse
from collections import defaultdict
import json
import logging
from pathlib import Path
import queue
import threading
import time

from pympler import asizeof
from typing import Any, List, Tuple
from datetime import datetime as dt

from src.models.configurations import AppConfig
from src.models.ethtool import EthtoolParser
from src.utils.commands import Command
from src.utils.ssh_connection import SshConnection
from src.enums.command_types import CommandTypes as ct


class Sample:
    begin: dt = None
    end: dt = None

    _interf: str
    _app_config: AppConfig
    _ssh_connection: SshConnection

    snapshot: Any = None

    def __init__(self, interf: str, app_config: AppConfig, ssh_connection: SshConnection) -> None:
        self._interf = interf
        self._app_config = app_config
        self._ssh_connection = ssh_connection

    def begin(self) -> None:
        self.begin = dt.now()

    def end(self) -> None:
        self.end = dt.now()

    def new(self, cmd: Command) -> Any:
        self.begin()
        match cmd.cmd_type:
            case ct.MODIFY, ct.SYSTEM, ct.COMMON:
                print("Not implemented...")
            case ct.ETHTOOL:
                self.snapshot = EthtoolParser(self._interf, self._app_config, self._ssh_connection).all_info()
            case ct.MLXLINK:
                print("Not implemented...")
            case ct.MLXCONFIG:
                print("Not implemented...")
            case ct.MST:
                print("Not implemented...")
            case _:
                print("Unknown command")
        self.end()

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

    def get_data_x(self) -> dt:
        return self._x_value

    def get_data_y(self) -> float:
        return self._y_value

    def get_label_y(self) -> str:
        return self._y_axis_label


class Worker(threading.Thread):
    _MAX_RECONNECT = 10

    _start: dt = None
    _stop: dt = None

    _interf: str
    _app_config: AppConfig
    _ssh_connection: SshConnection

    _collected_samples: queue.Queue = queue.Queue()
    _extracted_samples: list[Sample] = []

    def __init__(
        self, cmd: Command, interf: str, app_config: AppConfig, ssh_connection: SshConnection, name: str = "Worker"
    ) -> None:
        super().__init__(name=name, daemon=True)  # daemon=True means it won’t block program exit
        self._cmd = cmd
        self._stop_event = threading.Event()

        self._interf = interf
        self._app_config = app_config
        self._ssh_connection = ssh_connection

    def run(self) -> None:
        """Thread main logic (executed when start() is called)."""
        self.work_start()
        reconnect = 1
        while not self._stop_event.is_set():
            try:
                if reconnect > self._MAX_RECONNECT:
                    logging.info(f"Reconnect failed 10 times. Exiting thread...")
                    reconnect = 0
                    self.stop()
                    break
                sample = Sample(self._interf, self._app_config, self._ssh_connection).new(self._cmd)
                self._collected_samples.put(sample)
                time.sleep(self._app_config.system.get_command_update_value())
            except KeyboardInterrupt:
                logging.info(f"User pressed 'Ctrl+c' - Exiting worker thread")
            except Exception as e:
                logging.exception(f"Collection stopped unexpectedly: {e}")
                try:
                    self._ssh_connection.connect()
                    if self._ssh_connection.is_connected():
                        logging.info(f"Reconnected to SSH session")
                    else:
                        logging.exception(f"Failed to reconnect to SSH session ({reconnect}/{self._MAX_RECONNECT})")
                except Exception as e:
                    logging.exception(f"SSH reconnect failed: {e}")
            reconnect += 1
        self.work_stop()

    def stop(self) -> None:
        self._stop_event.set()
        logging.debug(f"Stop event set")

    def stop_and_wait(self) -> None:
        self._stop_event.set()
        while self.is_alive():
            time.sleep(0.1)

    def stopped(self) -> bool:
        """Return True if stop signal is active."""
        return self._stop_event.is_set()

    def work_start(self) -> None:
        self._start = dt.now()

    def get_work_start(self) -> None:
        return self._start

    def work_stop(self) -> None:
        self._stop = dt.now()

    def get_work_stop(self) -> None:
        return self._stop

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
        logging.debug("Clearing extracted samples")

    def log_extracted_size(self):
        logging.debug(f"Extracted list size: {len(self._extracted_samples)}")
        logging.debug(
            f"Mem size of extracted list: {round(asizeof.asizeof(self._extracted_samples) / (1024 * 1024), 2)} Mb"
        )

    def get_all_samples(self) -> list[Sample]:
        self._collect_all_samples()
        self.log_extracted_size()
        return self._extracted_samples

    def get_first_sample(self) -> Sample:
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
        return [s for s in self.collected_samples.get() if hasattr(s, "_begin") and start <= s._begin <= end]

    def group_by_type(self) -> dict:
        """Group samples by their concrete class name."""
        groups = defaultdict(list)
        for s in self.collected_samples.get():
            groups[type(s).__name__].append(s)
        return dict(groups)

    def export_json(self, full_path: Path) -> None:
        with full_path.open("w", encoding="utf-8") as f:
            json.dump(self.get_samples(), f, default=str, indent=2)

    def summary(self) -> str:
        """One‑line textual summary of the collected sample data."""
        total_samples = len(self._collected_samples)
        types = {type(s).__name__ for s in self._collected_samples.get()}
        return f"Collected {total_samples} samples of types: {', '.join(sorted(types))}"


class WorkManager:
    _work_pool: List[Worker]

    def __init__(self) -> None:
        self._work_pool = []

    def add(self, new_worker: Worker) -> None:
        old_worker = self.get_worker(new_worker._interf)
        if old_worker is None:
            new_worker.start()
            self._work_pool.append(new_worker)
        else:
            old_worker.start()
            logging.debug(f"Worker already exists for: {old_worker._interf}")

    def clear(self) -> None:
        logging.debug(f"Clearing {len(self._work_pool)} workers from pool")
        self._work_pool.clear()
        logging.debug(f"Work pool cleared")

    def stop_all(self) -> None:
        logging.debug(f"Stop all workers in pool: {len(self._work_pool)}")
        for w in self._work_pool:
            w.stop()
            logging.debug(f"Thread stopped")
            w.join()
            logging.debug(f"Thread joined")

    def reset(self) -> None:
        logging.debug("Reset work manager")
        self.stop_all()
        self.clear()
        logging.debug("Work manager has been resetted")

    def get_worker(self, interf: str) -> Worker | None:
        for w in self._work_pool:
            if w._interf == interf:
                logging.debug(f"Found worker: {w._interf}")
                return w
        logging.debug(f"Did not find any old worker for interface: {interf}")
        return None

    def summary(self) -> str:
        """One‑line textual summary of the work pool."""
        total_workers = len(self._work_pool)
        types = {type(s).__name__ for s in self._work_pool}
        return f"Started {total_workers} workers of types: {', '.join(sorted(types))}"
