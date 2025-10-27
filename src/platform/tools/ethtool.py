from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.interfaces.connection import CommandResult
from src.interfaces.tool import ITool, Tool
from src.platform.enums.software import CommandInputType, ToolType


class EthtoolTool(Tool, ITool):
    """Ethtool class for CLI diagnostic tools."""

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["sudo", "ethtool", CommandInputType.INTERFACE],
        #["ethtool", "-v", "-s", CommandInputType.INTERFACE],
        ["ethtool", "-i", CommandInputType.INTERFACE],
        ["ethtool", "-S", CommandInputType.INTERFACE],  # Statistics
        ["ethtool", "-m", CommandInputType.INTERFACE],  # Temp, Volt
        ["ethtool", "-k", CommandInputType.INTERFACE],  # Features
        ["ethtool", "-g", CommandInputType.INTERFACE],  # Features
        ["ethtool", "-c", CommandInputType.INTERFACE],  # Coalesce
    ]
    # fmt: on

    def __init__(self, ssh_connection: SshConnection, interfaces: list[str]):
        """Initialize tool with SSH connection and interfaces.

        Args:
            ssh_connection: SSH connection for command execution
            interfaces: List of network interface names
        """
        Tool.__init__(self, ssh_connection)
        self._interfaces = interfaces

    @property
    def type(self) -> ToolType:
        """Name of the CLI tool."""
        return ToolType.ETHTOOL

    def available_commands(self) -> list[str]:
        """Get available commands for this tool.

        Returns:
            list of CLI commands
        """
        commands_modified = []
        for interface in self._interfaces:
            for command in self._AVAILABLE_COMMANDS:
                commands_modified.append(self._generate_commands(interface, command))

        return commands_modified

    def execute(self) -> None:
        for command in self.available_commands():
            self._execute(command)

    def log(self) -> None:
        self._log()

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
        available_commands = self.available_commands()

        response = {}
        for interface in self._interfaces:
            for command_config in available_commands:
                for cmd_type, args in command_config.items():
                    target = interface
                    if cmd_type != CommandInputType.INTERFACE:
                        continue

                    final_command = f"{' '.join(args)} {target}"
                    result = self._execute(final_command)
                    if result.success:
                        response[interface] = result.stdout.strip()
                    else:
                        response[interface] = CommandResult.error(result.stderr, result.return_code)
        return response
