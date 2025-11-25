import logging
from typing import Any, ClassVar

from src.core.connect import SshConnection
from src.core.result import CmdResult
from src.core.tool import Tool
from src.interfaces.component import ITool
from src.platform.enums.software import CmdInputType, ToolType


class MstTool(Tool, ITool):
    """Mellanox Software Tools (MST) diagnostic tool.

    Provides access to MST commands for starting the MST service and
    querying device status.
    """

    # fmt: off
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["mst", "start"],
        ["mst", "status"]
        #["mst", "stop"],
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
            ToolType: ToolType.MST constant
        """
        return ToolType.MST

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
        """Execute all available MST commands.

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
            dict[str, str]: Dictionary with raw_output key containing unparsed output
        """
        return {"raw_output": output}

    def _summarize(self) -> dict[str, Any]:
        """Execute all commands and return parsed results.

        Returns:
            dict[str, Any]: Dictionary mapping command types to results or error objects
        """
        available_commands = self.available_cmds()

        response = {}
        for command_cfg in available_commands:
            for cmd_type, args in command_cfg.items():
                target = ""
                if cmd_type != CmdInputType.NOT_USED:
                    continue
                final_command = f"{' '.join(args)} {target}"
                result = self._exec(final_command)
                if result.success:
                    response[CmdInputType.NOT_USED.value] = result.stdout
                else:
                    response[CmdInputType.NOT_USED.value] = CmdResult.error(
                        result.stderr, result.rcode
                    )
        return response
