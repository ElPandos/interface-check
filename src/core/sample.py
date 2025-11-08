from datetime import datetime as dt
import logging

from src.core.connect import SshConnection
from src.interfaces.component import ITime
from src.core.tool import Tool
from src.models.config import Config
from src.platform.enums.log import LogName


class Sample(Tool, ITime):
    def __init__(self, config: Config, ssh_connection: SshConnection) -> None:
        Tool.__init__(self, ssh_connection)
        ITime.__init__(self)

        self._snapshot: str = ""
        self._config = config

        self._logger = logging.getLogger(LogName.MAIN.value)

    @property
    def snapshot(self) -> "Sample":
        return self._snapshot

    @snapshot.setter
    def snapshot(self, value: str) -> None:
        self._snapshot = value

    def collect(self, worker_command: str) -> "Sample":
        self.start_timer()

        result = self._exec(worker_command.command)
        if result.success:
            self._snapshot = result.str_out
        else:
            self._logger.exception("Command execution failed")

        self.stop_timer()

        return self


class PlotSampleData:
    def __init__(self, sample: Sample, source: str, value: str) -> None:
        self._x_value: dt = None
        self._y_value: float = None

        self._y_label: str = ""

        snap = sample.snapshot[source]  # Source needs to be verified
        snap_value = snap[value]

        # If the data contains xxx / yyy then it will be seperated into e.g. Celsuius / Farenheit
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
        return self._y_label
