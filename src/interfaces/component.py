"""Component interfaces for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime as dt
import logging
import re
from typing import TYPE_CHECKING, Any, ClassVar

from src.core.result import CmdResult

if TYPE_CHECKING:
    from src.platform.enums.software import ToolType


class IParser(ABC):
    """Abstract interface for command output parsers.

    Provides base functionality for parsing command output into structured data.
    """

    _ansi_escape: ClassVar[re.Pattern] = re.compile(r"\x1b\[[0-9;]*m")

    def __init__(self, log_name: str):
        """Initialize parser with logger.

        Args:
            log_name: Logger name for this parser
        """
        self._logger = logging.getLogger(log_name)

    def _log_parse(self, raw_data: str) -> None:
        """Common parse logging for all parsers.

        Args:
            raw_data: Raw input data being parsed
        """
        clean_data = self._ansi_escape.sub("", raw_data).strip()
        preview = clean_data[:200] if len(clean_data) > 200 else clean_data
        self._logger.debug(f"[{self.name}] Parsing:\n\n{preview}{'...' if len(clean_data) > 200 else ''}\n")

    @property
    @abstractmethod
    def name(self) -> str:
        """Get parser name identifier.

        Returns:
            str: Parser name
        """

    @abstractmethod
    def parse(self, raw_data: str) -> Any:
        """Parse raw data into structured format.

        Args:
            raw_data: Raw data to parse

        Returns:
            Any: Parsed data structure
        """

    @abstractmethod
    def get_result(self) -> Any:
        """Get parsed result.

        Returns:
            Any: Parsed result data
        """

    @abstractmethod
    def log(self) -> None:
        """Log parsed content to logger."""


class ITool(ABC):
    """Abstract interface for diagnostic tools.

    Provides base functionality for network diagnostic tools like ethtool,
    mlxlink, and other command-line utilities.
    """

    @property
    @abstractmethod
    def type(self) -> "ToolType":
        """Get tool type identifier.

        Returns:
            ToolType: Tool type enum value
        """

    @abstractmethod
    def _parse(self, cmd: str, output: str) -> dict[str, str]:
        """Parse command output into structured data.

        Args:
            cmd: Command that was executed
            output: Raw output from command execution

        Returns:
            dict[str, str]: Parsed data as dictionary
        """

    @abstractmethod
    def available_cmds(self) -> list[str]:
        """Get available commands for the tool.

        Returns:
            list[str]: List of command strings
        """

    @abstractmethod
    def execute(self) -> None:
        """Execute all available commands for the tool."""

    @abstractmethod
    def log(self, logger: logging.Logger) -> None:
        """Log all results for the tool.

        Args:
            logger: Logger instance for output
        """

    @abstractmethod
    def _summarize(self) -> dict[str, Any]:
        """Summarize all command results.

        Returns:
            dict[str, Any]: Summary of all results
        """


class IConnection(ABC):
    """Abstract interface for remote connections.

    Provides base functionality for SSH and other remote connection types.
    """

    @abstractmethod
    def connect(self) -> bool:
        """Connect to remote host.

        Returns:
            bool: True if connection successful, False otherwise
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from remote host and clean up resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """

    @abstractmethod
    def exec_cmd(self, cmd: str, timeout: int | None = None) -> CmdResult:
        """Execute command and return result.

        Args:
            cmd: Command to execute
            timeout: Optional timeout in seconds

        Returns:
            CmdResult: Command execution result
        """


class ITime:
    """Mixin for classes that track begin/end timestamps.

    Provides centralized time tracking with duration calculation.
    Not an ABC since it provides concrete implementations.
    """

    def __init__(self):
        """Initialize time tracking with None timestamps."""
        self._begin: dt | None = None
        self._end: dt | None = None

    def start_timer(self) -> dt:
        """Mark begin time.

        Returns:
            Begin timestamp
        """
        self._begin = dt.now(UTC)
        return self._begin

    def stop_timer(self) -> dt:
        """Mark end time.

        Returns:
            End timestamp
        """
        self._end = dt.now(UTC)
        return self._end

    @property
    def begin(self) -> dt | None:
        """Get begin timestamp.

        Returns:
            dt | None: Begin timestamp or None if not started
        """
        return self._begin

    @property
    def end(self) -> dt | None:
        """Get end timestamp.

        Returns:
            dt | None: End timestamp or None if not stopped
        """
        return self._end

    @property
    def duration(self) -> float | None:
        """Calculate duration in seconds.

        Returns:
            float | None: Duration in seconds, or None if times not set
        """
        if self._begin and self._end:
            return (self._end - self._begin).total_seconds()
        return None

    @property
    def duration_str(self) -> str:
        """Get human-readable duration string.

        Returns:
            Formatted duration or status message
        """
        if not self._begin:
            return "Not started"
        if not self._end:
            return "In progress"
        return str(self._end - self._begin)
