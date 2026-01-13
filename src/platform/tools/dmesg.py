"""Dmesg CLI tool implementation."""

from dataclasses import dataclass
from datetime import datetime as dt
import logging
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.core.tool import Tool
from src.interfaces.component import ITool
from src.platform.enums.software import ToolType


@dataclass(frozen=True)
class DmesgEntry:
    """Represents a single dmesg log entry.

    Attributes:
        timestamp: Entry timestamp or None if not parsed
        facility: Log facility (typically 'kernel')
        level: Log level (e.g., 'info', 'warn', 'error')
        message: Log message content
    """

    timestamp: dt | None
    facility: str
    level: str
    message: str


class DmesgTool(Tool, ITool):
    """Dmesg kernel message diagnostic tool.

    Provides access to kernel ring buffer messages, filtered for network-related
    events including Mellanox adapters, SFP/QSFP modules, and ethernet interfaces.
    """

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["dmesg", "-T", "|", "egrep", "-i", "'mlx|mellanox|sfp|qsfp|phy|eth|port'", "|", "tail", "-n", "100" ],
    ]
    # fmt: on

    def __init__(self, ssh: SshConnection, interfaces: list[str], logger=None):
        """Initialize tool with SSH connection.

        Args:
            ssh: SSH connection for command execution
            interfaces: List of network interfaces (unused for dmesg)
        """
        Tool.__init__(self, ssh, logger)
        self._interfaces = interfaces

    @property
    def type(self) -> ToolType:
        """Get the tool type identifier.

        Returns:
            ToolType: ToolType.DMESG constant
        """
        return ToolType.DMESG

    def available_cmds(self) -> list[str]:
        """Get available commands for this tool.

        Returns:
            list[str]: List of CLI command strings
        """
        commands_modified = []
        for command in self._AVAILABLE_COMMANDS:
            commands_modified.append(" ".join(command))

        return commands_modified

    def execute(self) -> None:
        """Execute all available dmesg commands.

        Runs each command from available_cmds() and stores results.
        """
        for command in self.available_cmds():
            self._exec(command)

    def log(self, logger: logging.Logger) -> None:
        """Log all command results.

        Args:
            logger: Logger instance for output
        """
        self._log(logger)

    def _parse(self, _command_name: str, output: str) -> list[DmesgEntry]:
        """Parse dmesg entries with timestamps.

        Args:
            _command_name: Command name (unused)
            output: Raw dmesg output

        Returns:
            list[DmesgEntry]: List of parsed DmesgEntry objects
        """
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
                            timestamp = dt.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.UTC)
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
        """Summarize tool results.

        Returns:
            dict[str, Any]: Dictionary mapping commands to parsed results
        """
        return {}
