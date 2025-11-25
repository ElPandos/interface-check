import logging
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.core.result import CmdResult
from src.core.tool import Tool
from src.interfaces.component import ITool
from src.platform.enums.software import CmdInputType, ToolType


class MlxTool(Tool, ITool):
    """Mellanox diagnostic tool for mlxlink and mlxconfig commands.

    Provides access to Mellanox-specific diagnostic commands for querying
    adapter configuration and link status.
    """

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["mlxlink", "-d", CmdInputType.MST_PCICONF],
        ["mlxconfig", "-d", CmdInputType.MST_PCICONF, "query"]
    ]
    # fmt: on

    def __init__(self, ssh: SshConnection, interfaces: list[str], logger=None):
        """Initialize tool with SSH connection and interfaces.

        Args:
            ssh: SSH connection for command execution
            interfaces: List of network interface names
        """
        Tool.__init__(self, ssh, logger)
        self._interfaces = interfaces

    @property
    def type(self) -> ToolType:
        """Get the tool type identifier.

        Returns:
            ToolType: ToolType.MLX constant
        """
        return ToolType.MLX

    def available_cmds(self) -> list[str]:
        """Get available commands for this tool.

        Returns:
            list[str]: List of command dictionaries with interface mappings
        """
        commands_modified = []
        for interface in self._interfaces:
            for command in self._AVAILABLE_COMMANDS:
                commands_modified.append(self._gen_cmds(interface, command))

        return commands_modified

    def execute(self) -> None:
        """Execute all available mlx commands.

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

    def _parse(self, cmd: str, output: str) -> dict[str, str]:
        """Parse raw command output into structured data.

        Args:
            cmd: Executed command string
            output: Raw stdout from command execution

        Returns:
            dict[str, str]: Dictionary with raw_output key containing unparsed output
        """
        return {"raw_output": output}

    def _summarize(self) -> dict[str, Any]:
        """Execute all commands and return parsed results.

        Returns:
            dict[str, Any]: Dictionary mapping interface names to command results or error objects
        """
        available_commands = self.available_cmds()

        response = {}
        for interface in self._interfaces:
            for command_cfg in available_commands:
                for cmd_type, args in command_cfg.items():
                    target = interface
                    if cmd_type == CmdInputType.MST_PCICONF:
                        target = get_pci_id_command(interface)

                    final_command = f"{' '.join(args)} {target}"
                    result = self._exec(final_command)
                    if result.success:
                        response[interface] = result.stdout
                    else:
                        response[interface] = CmdResult.error(result.stderr, result.rcode)
        return response
