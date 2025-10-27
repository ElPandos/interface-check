"""Connection interface for abstracting SSH and other remote connections."""

from abc import ABC, abstractmethod


class CommandResult:
    """Result of a command execution."""

    def __init__(
        self,
        command: str = "",
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0,
        execution_time: float = 0.0,
    ):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.execution_time = execution_time

    @property
    def success(self) -> bool:
        """Indicates whether the command executed successfully."""
        return self.return_code == 0 and not self.stderr.strip()

    @staticmethod
    def error(command: str, message: str, return_code: int = -1) -> "CommandResult":
        """
        Create a default error CommandResult for failed or skipped executions.

        Args:
            command: The command that failed.
            message: Description or error message.
            return_code: Optional custom error code (default: -1).

        Returns:
            CommandResult instance representing a failed command.
        """
        return CommandResult(
            command=command,
            stdout="",
            stderr=message.strip(),
            return_code=return_code,
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
