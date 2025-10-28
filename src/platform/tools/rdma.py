from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.interfaces.connection import CommandResult
from src.interfaces.tool import ITool, Tool
from src.platform.enums.software import CommandInputType, ToolType


class RdmaTool(Tool, ITool):
    """Rdma class for CLI diagnostic tools."""

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["sudo", "rdma", "dev", "show"]
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
        """Name of the CLI tool."""
        return ToolType.RDMA

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
                        result.stderr, result.return_code
                    )
        return response
