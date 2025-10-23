import json
import logging
from pathlib import Path
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.interfaces.connection import CommandResult
from src.interfaces.tool import ITool
from src.platform.enums.software import CommandInputType


class RdmaTool(ITool):
    """Abstract base class for CLI diagnostic tools."""

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[str]]] = [
        ["rdma", "dev", "show"]
    ]
    # fmt: on

    def __init__(self, ssh_connection: SshConnection):
        """Initialize tool with SSH connection and interfaces.

        Args:
            ssh_connection: SSH connection for command execution
            interfaces: List of network interface names
        """
        self._ssh_connection = ssh_connection

        self._results: dict[str, Any] = {}

        self.logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        """Name of the CLI tool."""
        return "rdma"

    def get_available_commands(self) -> list[dict[CommandInputType, list[str]]]:
        """Get available commands for this tool.

        Returns:
            Dict mapping command names to CLI commands
        """
        return self._AVAILABLE_COMMANDS

    def _execute(self, command: str) -> CommandResult:
        """Execute a specific command and return result.

        Args:
            command: CLI command to execute

        Returns:
            CommandResult with execution details
        """
        if not self._ssh_connection.is_connected():
            message = f"Cannot execute command '{command}': No SSH connection"
            self.logger.error(message)
            return CommandResult.error(command, message)

        try:
            result = self._ssh_connection.execute_command(command)
            if result.success:
                self.logger.info(f"Succesfully executed command: {command}")
            else:
                return CommandResult.error(command, result.stderr)
        except Exception as e:
            return CommandResult.error(command, e)

        return CommandResult(
            stdout=result.stdout, stderr=result.stderr, exit_status=result.exit_status
        )

    def _parse(self, command: str, output: str) -> dict[str, str]:
        """Parse raw command output into structured data.

        Args:
            command: Name of the executed command
            output: Raw stdout from command execution

        Returns:
            ToolResult with parsed data
        """
        return {"raw_output": output}

    def _summarize(self) -> dict[str, Any]:
        """Execute all commands and return parsed results.

        Returns:
            Dict mapping command names to parsed data
        """
        available_commands = self.get_available_commands()

        response = {}
        for command_config in available_commands:
            for cmd_type, args in command_config.items():
                target = ""
                if cmd_type != CommandInputType.NOT_USED:
                    continue
                final_command = f"{' '.join(args)} {target}"
                result = self._execute(final_command)
                if result.success:
                    response[CommandInputType.NOT_USED.value] = result.stdout.strip()
                else:
                    response[CommandInputType.NOT_USED.value] = CommandResult.error(
                        result.stderr, result.exit_status
                    )
        return response

    def _check_response(
        self, interface: str, response: dict[str, Any], result: CommandResult
    ) -> None:
        if result.success:
            response[interface] = result.stdout.strip()
        else:
            response[interface] = CommandResult.error(result.stderr, result.exit_status)

    def log_summary(self) -> None:
        data = self.summarize()

        for interface, output in data:
            self.logger.info("==================")
            self.logger.info(f"== {interface}")
            self.logger.info("==================")
            self.logger.info(f"\n{output}")

    def save(self, path: Path) -> None:
        """Export collected data to JSON file.

        Args:
            output_path: Path to output file
        """
        with open(path, "w") as f:
            json.dump(self._summarize(), f, indent=2)
