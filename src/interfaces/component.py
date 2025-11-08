"""Component interfaces for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime as dt
import logging
from typing import TYPE_CHECKING, Any

from src.interfaces.connection import CmdResult

if TYPE_CHECKING:
    from src.platform.enums.software import ToolType


class IParser(ABC):
    """Abstract interface for parsers."""

    def __init__(self, log_name: str):
        self._logger = logging.getLogger(log_name)

    @property
    @abstractmethod
    def name(self) -> str:
        """Parser name identifier."""

    @abstractmethod
    def _parse(self) -> Any:
        """Parse data."""

    @abstractmethod
    def get_result(self) -> Any:
        """Get parsed result."""

    @abstractmethod
    def log(self) -> None:
        """Log parsed content."""


class ITool(ABC):
    """Abstract interface for tools."""

    @property
    @abstractmethod
    def type(self) -> "ToolType":
        """Tool type identifier."""

    @abstractmethod
    def _parse(self, command: str, output: str) -> dict[str, str]:
        """Parse function to build output data to structured data.

        Args:
            command: Command that was executed
            output: Raw output from command execution

        Returns:
            Parsed data as dictionary
        """

    @abstractmethod
    def get_available_commands(self) -> list[list[str]]:
        """Get available commands for the tool."""

    @abstractmethod
    def execute(self) -> None:
        """Execute all commands for the tool."""

    @abstractmethod
    def log(self) -> None:
        """Log all results for the tool."""

    @abstractmethod
    def _summarize(self) -> dict[str, Any]:  # Needed?
        """Summarizes the results."""


class IConnection(ABC):
    """Abstract interface for connections."""

    @abstractmethod
    def connect(self) -> bool:
        """Connect to host. Returns if it was successful or not."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from host and cleans up resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""

    @abstractmethod
    def execute_command(self, command: str, timeout: int | None = None) -> CmdResult:
        """Execute command and return command result.

        Args:
            command: Command to execute
            timeout: Optional timeout in seconds

        Returns:
            Command execution result
        """


class ITime(ABC):
    """Mixin for classes that track begin/end timestamps.

    Provides centralized time tracking with duration calculation.
    """

    def __init__(self):
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
        """Get begin timestamp."""
        return self._begin

    @property
    def end(self) -> dt | None:
        """Get end timestamp."""
        return self._end

    @property
    def duration(self) -> float | None:
        """Calculate duration in seconds.

        Returns:
            Duration in seconds, or None if times not set
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
