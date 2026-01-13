from datetime import datetime as dt

from src.core.connect import SshConnection
from src.core.enum.messages import LogMsg
from src.core.tool import Tool
from src.interfaces.component import ITime
from src.models.config import Config


class Sample(Tool, ITime):
    """Data sample collector.

    Args:
        cfg: Application configuration
        ssh: SSH connection for command execution
    """

    def __init__(self, cfg: Config, ssh: SshConnection) -> None:
        Tool.__init__(self, ssh)
        ITime.__init__(self)

        self._snapshot: str = ""
        self._cfg = cfg
        self._cmd_result = None

    @property
    def snapshot(self) -> "Sample":
        """Get snapshot data.

        Returns:
            Snapshot data
        """
        return self._snapshot

    @snapshot.setter
    def snapshot(self, value: str) -> None:
        """Set snapshot data.

        Args:
            value: Snapshot data
        """
        self._snapshot = value

    def collect(self, worker_command: str, logger=None) -> "Sample":
        """Collect sample by executing command.

        Args:
            worker_command: Command to execute
            logger: Optional logger to use for command execution

        Returns:
            Self with collected data
        """
        self.start_timer()

        # Check if time command should be used
        time_cmd = hasattr(self._cfg, "sut_time_cmd") and self._cfg.sut_time_cmd
        use_shell = hasattr(worker_command, "use_shell") and worker_command.use_shell

        result = self._exec(worker_command.command, use_time_cmd=time_cmd, use_shell=use_shell, logger=logger)
        self._cmd_result = result

        if result.success:
            self._snapshot = result.stdout
        else:
            self._logger.error(f"{LogMsg.SAMPLE_CMD_FAIL.value}: {result.stderr or 'No output'}")
            self._snapshot = ""

        self.stop_timer()

        return self

    @property
    def cmd_result(self):
        """Get command result with timing data.

        Returns:
            CmdResult instance
        """
        return self._cmd_result


class PlotSampleData:
    """Plot data extracted from sample.

    Args:
        sample: Sample to extract data from
        source: Data source key
        value: Value key
    """

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
        """Get X axis value.

        Returns:
            Timestamp
        """
        return self._x_value

    @property
    def y(self) -> float:
        """Get Y axis value.

        Returns:
            Numeric value
        """
        return self._y_value

    @property
    def y_label(self) -> str:
        """Get Y axis label.

        Returns:
            Label string
        """
        return self._y_label
