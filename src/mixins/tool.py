"""Tool interface for CLI-based network diagnostic tools."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
import time
from typing import Any

from src.utils.ssh_connection import SshConnection


@dataclass(frozen=True)
class CommandResult:
    """Result of a command execution."""

    command: str
    stdout: str
    stderr: str
    success: bool
    execution_time: float


class Tool(ABC):
    """Abstract base class for CLI diagnostic tools."""

    def __init__(self, ssh_connection: SshConnection, interface: str | None = None):
        """Initialize tool with SSH connection and optional interface.

        Args:
            ssh_connection: SSH connection for command execution
            interface: Network interface name (e.g., 'eth0')
        """
        self.ssh_connection = ssh_connection
        self.interface = interface
        self._cached_data: dict[str, Any] = {}

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the CLI tool (e.g., 'ethtool', 'mlxconfig')."""

    @abstractmethod
    def get_commands(self) -> dict[str, str]:
        """Get available commands for this tool.

        Returns:
            Dict mapping command names to CLI commands
        """

    @abstractmethod
    def parse_output(self, command_name: str, raw_output: str) -> Any:
        """Parse raw command output into structured data.

        Args:
            command_name: Name of the executed command
            raw_output: Raw stdout from command execution

        Returns:
            Parsed data structure specific to the tool
        """

    def execute_command(self, command_name: str, timeout: int = 30) -> CommandResult:
        """Execute a specific command and return result.

        Args:
            command_name: Name of command from get_commands()
            timeout: Command timeout in seconds

        Returns:
            CommandResult with execution details
        """
        commands = self.get_commands()
        if command_name not in commands:
            raise ValueError(f"Unknown command: {command_name}")

        command = commands[command_name]
        if self.interface:
            command = command.format(interface=self.interface)

        start_time = time.perf_counter()

        try:
            stdout, stderr = self.ssh_connection.exec_command(command, timeout=timeout)
            success = len(stderr.strip()) == 0
        except (RuntimeError, OSError, TimeoutError) as e:
            stdout, stderr = "", f"Command failed: {e}"
            success = False

        execution_time = time.perf_counter() - start_time

        return CommandResult(
            command=command, stdout=stdout, stderr=stderr, success=success, execution_time=execution_time
        )

    def collect_all(self) -> dict[str, Any]:
        """Execute all commands and return parsed results.

        Returns:
            Dict mapping command names to parsed data
        """
        results = {}
        for command_name in self.get_commands():
            try:
                result = self.execute_command(command_name)
                if result.success:
                    results[command_name] = self.parse_output(command_name, result.stdout)
                else:
                    results[command_name] = None
            except (ValueError, RuntimeError, OSError):
                results[command_name] = None

        self._cached_data.update(results)
        return results

    def export_data(self, output_path: Path) -> None:
        """Export collected data to JSON file.

        Args:
            output_path: Path to output file
        """
        data = self._cached_data if self._cached_data else self.collect_all()

        with output_path.open("w") as f:
            json.dump(data, f, indent=2, default=str)
