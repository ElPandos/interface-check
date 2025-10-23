"""Tool interface for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.interfaces.connection import CommandResult


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution."""

    def __init__(self, command: str, data: Any, error: str, execution_time: float):
        self.command = command
        self.data = data
        self.error = error
        self.execution_time = execution_time

    @property
    def success(self) -> bool:
        """Indicates whether the command executed successfully."""
        return self.error.strip() == ""

    # @staticmethod
    # def error(command: str, message: str, exit_status: int = -1) -> "CommandResult":
    #     """
    #     Create a default error CommandResult for failed or skipped executions.

    #     Args:
    #         command: The command that failed.
    #         message: Description or error message.
    #         exit_status: Optional custom error code (default: -1).

    #     Returns:
    #         CommandResult instance representing a failed command.
    #     """
    #     return CommandResult(
    #         command=command,
    #         stdout="",
    #         stderr=message.strip(),
    #         exit_status=exit_status,
    #         execution_time=0.0,
    #     )


class ITool(ABC):
    """Abstract interface for diagnostic tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""

    @abstractmethod
    def get_available_commands(self) -> dict[str, str]:
        """Get available commands for this tool."""

    @abstractmethod
    def _execute(self, command: str) -> CommandResult:
        """Execute a tool command."""

    @abstractmethod
    def _parse(self, command: str, output: str) -> dict[str, str]:
        """Parse tool output into structured data."""

    @abstractmethod
    def _summarize(self) -> dict[str, Any]:
        """Summarize tool results."""

    @abstractmethod
    def log_summary(self) -> None:
        """Log summary of tool results."""

    @abstractmethod
    def save(self, path: Path) -> None:
        """Save results to file."""
