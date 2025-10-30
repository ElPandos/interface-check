"""Tool interface for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import itertools
import logging
from pathlib import Path
from typing import Any

from src.core import json
from src.core.connect import SshConnection
from src.interfaces.connection import CommandResult
from src.platform.enums.log import LogName
from src.platform.enums.software import CommandInputType, ToolType
from src.platform.tools import helper


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


class ITool(ABC):
    """Abstract interface for diagnostic tools."""

    @property
    @abstractmethod
    def type(self) -> ToolType:
        """Tool name identifier."""

    @abstractmethod
    def available_commands(self) -> list[list[str]]:
        """Get available commands for this tool."""

    @abstractmethod
    def execute(self) -> None:
        """Execute all commands for tool."""

    @abstractmethod
    def log(self) -> None:
        """Log all commands results for tool."""

    @abstractmethod
    def _parse(self, command: str, output: str) -> dict[str, str]:
        """Parse tool output into structured data."""

    @abstractmethod
    def _summarize(self) -> dict[str, Any]:
        """Summarize tool results."""


class Tool:
    def __init__(self, ssh_connection: SshConnection):
        self._ssh_connection = ssh_connection
        self._results: dict[str, CommandResult] = {}

        self._logger = logging.getLogger(LogName.MAIN.value)

    def _execute(self, command: str) -> CommandResult | None:
        """Execute a specific command and return result.

        Args:
            command: CLI command to execute
        """
        result = None
        if not self._ssh_connection.is_connected():
            message = f"Cannot execute command '{command}': No SSH connection"
            self._logger.error(message)
            result = CommandResult.error(command, message)
            self._results[command] = result
            return result

        try:
            result = self._ssh_connection.execute_command(command)
            if result.success:
                self._logger.debug(f"Succesfully executed command: {command}")
            else:
                result = CommandResult.error(command, result.stderr)
        except Exception as e:
            result = CommandResult.error(command, e)

        self._results[command] = result

        return result

    def _generate_commands(self, interface: str, command: list[Any]) -> str:
        command_modified = []
        for part in command:
            match part:
                case CommandInputType.INTERFACE:
                    command_modified.append(interface)
                case CommandInputType.MST_PCICONF:
                    command_modified.append(helper.get_mst_device(self._ssh_connection, interface))
                case CommandInputType.PCI_ID:
                    command_modified.append(helper.get_pci_id(self._ssh_connection, interface))
                case _:
                    command_modified.append(part)

        return " ".join(command_modified)

    def _log(self) -> None:
        for command, result in self._results.items():
            if result.success:
                border = "".join(itertools.repeat("=", len(f"= {command}") + 2))
                self._logger.info(border)
                self._logger.info(f"= {command}")
                self._logger.info(border)
                self._logger.info(f"\n\n{result.stdout}")
            else:
                border = "".join(itertools.repeat("=", len(f"= {command} -> FAILED") + 2))
                self._logger.warning(border)
                self._logger.warning(f"= {command} -> FAILED")
                self._logger.warning(f"= Reason: {result.stderr}")
                self._logger.warning(border)

    def _save(self, path: Path) -> None:
        """Export collected data to JSON file.

        Args:
            path: Path to output file
        """
        with open(path, "w") as f:
            json.dump(self._summarize(), f, indent=2)

    def _check_response(
        self, interface: str, response: dict[str, Any], result: CommandResult
    ) -> None:
        if result.success:
            response[interface] = result.stdout.strip()
        else:
            response[interface] = CommandResult.error(result.stderr, result.return_code)
