"""Tool interface for network diagnostic tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    """Result of a tool execution."""

    command: str
    data: Any
    success: bool
    error: str | None = None
    execution_time: float = 0.0


class ITool(ABC):
    """Abstract interface for diagnostic tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""

    @abstractmethod
    def get_commands(self) -> dict[str, str]:
        """Get available commands for this tool."""

    @abstractmethod
    def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute a tool command."""

    @abstractmethod
    def parse_output(self, command: str, output: str) -> Any:
        """Parse tool output into structured data."""


class IToolFactory(ABC):
    """Factory for creating tool instances."""

    @abstractmethod
    def create_tool(self, tool_name: str, **kwargs) -> ITool:
        """Create tool instance."""

    @abstractmethod
    def get_available_tools(self) -> list[str]:
        """Get list of available tools."""
