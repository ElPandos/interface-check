from datetime import UTC, datetime as dt
import logging
from typing import Any

from src.core.connect import SshConnection
from src.interfaces.tool import Tool
from src.models.config import Config
from src.platform.enums.log import LogName


class Sample(Tool):
    def __init__(self, config: Config, ssh_connection: SshConnection) -> None:
        super().__init__(ssh_connection)
        self._begin: dt = None
        self._end: dt = None

        self.snapshot: str = None

        self._config = config

        self.logger = logging.getLogger(LogName.MAIN.value)

    @property
    def begin(self) -> dt:
        return self._begin

    @property
    def end(self) -> dt:
        return self._end

    def collect(self, worker_command: str) -> Any:
        self._begin = dt.now(tz=UTC)

        result = self._execute(worker_command.command)
        if result.success:
            self.snapshot = result.stdout
        else:
            self.logger.exception("Command execution failed")

        self._end = dt.now(tz=UTC)

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
