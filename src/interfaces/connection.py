"""Connection interface for abstracting SSH and other remote connections."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    """Result of a command execution."""

    def __init__(
        self,
        command: str = "",
        stdout: str = "",
        stderr: str = "",
        exit_status: int = 0,
        execution_time: float = 0.0,
    ):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.exit_status = exit_status
        self.execution_time = execution_time

    @property
    def success(self) -> bool:
        """Indicates whether the command executed successfully."""
        return self.exit_status == 0 and not self.stderr.strip()

    @staticmethod
    def error(command: str, message: str, exit_status: int = -1) -> "CommandResult":
        """
        Create a default error CommandResult for failed or skipped executions.

        Args:
            command: The command that failed.
            message: Description or error message.
            exit_status: Optional custom error code (default: -1).

        Returns:
            CommandResult instance representing a failed command.
        """
        return CommandResult(
            command=command,
            stdout="",
            stderr=message.strip(),
            exit_status=exit_status,
            execution_time=0.0,
        )


class IConnection(ABC):
    """Abstract interface for remote connections."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection. Returns True if successful."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection and cleanup resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""

    @abstractmethod
    def execute_command(self, command: str, timeout: int | None = None) -> CommandResult:
        """Execute command and return result."""
