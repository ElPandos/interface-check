import logging
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.core.result import CmdResult
from src.core.tool import Tool
from src.interfaces.component import ITool
from src.platform.enums.software import CmdInputType, ToolType


class EthtoolTool(Tool, ITool):
    """Ethtool network interface diagnostic tool.

    Provides access to ethtool commands for querying network interface
    statistics, configuration, and hardware information.
    """

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["ethtool", CmdInputType.INTERFACE],
        #["ethtool", "-v", "-s", CommandInputType.INTERFACE],
        ["ethtool", "-i", CmdInputType.INTERFACE], # Interface
        ["ethtool", "-S", CmdInputType.INTERFACE], # Statistics
        ["ethtool", "-m", CmdInputType.INTERFACE], # Temp, Volt
        ["ethtool", "-k", CmdInputType.INTERFACE], # Features
        ["ethtool", "-g", CmdInputType.INTERFACE], # Features
        ["ethtool", "-c", CmdInputType.INTERFACE], # Coalesce
    ]
    # fmt: on

    def __init__(self, ssh: SshConnection, interfaces: list[str]):
        """Initialize tool with SSH connection and interfaces.

        Args:
            ssh: SSH connection for command execution
            interfaces: List of network interface names
        """
        Tool.__init__(self, ssh)

        self._interfaces = interfaces

    @property
    def type(self) -> ToolType:
        """Get the tool type identifier.

        Returns:
            ToolType.ETHTOOL constant
        """
        return ToolType.ETHTOOL

    def available_cmds(self) -> list[str]:
        """Get available commands for all configured interfaces.

        Returns:
            list[str]: List of command dictionaries with interface mappings
        """
        commands_modified = []
        for interface in self._interfaces:
            for command in self._AVAILABLE_COMMANDS:
                commands_modified.append(self._gen_cmds(interface, command))
        return commands_modified

    def execute(self) -> None:
        """Execute all available ethtool commands.

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

    def _parse(self, command: str, output: str) -> dict[str, str]:
        """Parse raw command output into structured data.

        Args:
            command: Executed command string
            output: Raw stdout from command execution

        Returns:
            Dictionary with raw_output key containing unparsed output
        """
        return {"raw_output": output}

    def _summarize(self) -> dict[str, Any]:
        """Execute all commands and return parsed results.

        Returns:
            Dictionary mapping interface names to command results or error objects
        """
        available_commands = self.available_cmds()

        response = {}
        for interface in self._interfaces:
            for command_cfg in available_commands:
                for cmd_type, args in command_cfg.items():
                    target = interface
                    if cmd_type != CmdInputType.INTERFACE:
                        continue

                    final_command = f"{' '.join(args)} {target}"
                    result = self._exec(final_command)
                    if result.success:
                        response[interface] = result.stdout
                    else:
                        response[interface] = CmdResult.error(result.stderr, result.rcode)
        return response
