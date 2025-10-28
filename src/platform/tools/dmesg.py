"""Dmesg CLI tool implementation."""

from datetime import datetime
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.interfaces.tool import ITool, Tool
from src.platform.enums.software import ToolType


class DmesgTool(Tool, ITool):
    """Dmesg kernel message diagnostic tool."""

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["sudo", "dmesg", "-T", "|", "egrep", "-i", "'mlx|mellanox|sfp|qsfp|phy|eth|port'", "|", "tail", "-n", "100" ],
        #["sudo", "dmesg", "|", "egrep", "-i", "'mlx|sfp|qsfp|phy"],
        #["sudo", "dmesg", "|", "egrep", "-i", "'mlx|mellanox|sfp|qsfp|phy|port'"]
    ]
    # fmt: on

    def __init__(self, ssh_connection: SshConnection, interfaces: list[str]):
        """Initialize tool with SSH connection.

        Args:
            ssh_connection: SSH connection for command execution
        """
        Tool.__init__(self, ssh_connection)
        self._interfaces = interfaces

    @property
    def type(self) -> ToolType:
        return ToolType.DMESG

    def available_commands(self) -> list[str]:
        """Get available commands for this tool.

        Returns:
            List of CLI commands
        """
        commands_modified = []
        for command in self._AVAILABLE_COMMANDS:
            commands_modified.append(" ".join(command))

        return commands_modified

    def execute(self) -> None:
        for command in self.available_commands():
            self._execute(command)

    def log(self) -> None:
        self._log()

    def _parse(self, command_name: str, output: str) -> Any:
        """Parse dmesg entries with timestamps."""
        entries = []
        lines = output.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue

            # Parse timestamp if present
            timestamp = None
            if line.startswith("["):
                try:
                    # Extract timestamp from [timestamp] format
                    end_bracket = line.find("]")
                    if end_bracket > 0:
                        timestamp_str = line[1:end_bracket]
                        # Handle both human readable and epoch formats
                        if timestamp_str.count(" ") >= 2:  # Human readable
                            timestamp = datetime.strptime(
                                timestamp_str[:19], "%Y-%m-%d %H:%M:%S"
                            ).replace(tzinfo=datetime.UTC)
                        message = line[end_bracket + 1 :].strip()
                    else:
                        message = line
                except (ValueError, IndexError):
                    message = line
            else:
                message = line

            entries.append(
                DmesgEntry(
                    timestamp=timestamp,
                    facility="kernel",
                    level="info",  # Default level
                    message=message,
                )
            )

        return entries

    def _summarize(self) -> dict[str, Any]:
        """Summarize tool results."""
