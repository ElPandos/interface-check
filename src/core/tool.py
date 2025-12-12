"""Tool interface for CLI-based network diagnostic tools."""

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Any

from src.core import json
from src.core.cli import PrettyFrame
from src.core.connect import SshConnection
from src.core.enum.messages import LogMsg
from src.core.result import CmdResult
from src.platform.enums.log import LogName
from src.platform.enums.software import CmdInputType
from src.platform.tools import helper


@dataclass(frozen=True)
class ToolResult:
    """Tool result of a command execution.

    Attributes:
        cmd: Command that was executed
        data: Output data from command execution
        error: Error message if execution failed
        exec_time: Execution time in seconds
    """

    def __init__(self, cmd: str, data: Any, error: str, exec_time: float):
        """Initialize tool result.

        Args:
            cmd: Command that was executed
            data: Output data
            error: Error message
            exec_time: Execution time in seconds
        """
        self._cmd = cmd
        self._data = data
        self._error = error
        self._exec_time = exec_time

    @property
    def success(self) -> bool:
        """Indicates whether the tool was executed successfully.

        Returns:
            True if no error occurred, False otherwise
        """
        return not self._error.strip()


class Tool:
    """Base class for CLI-based network diagnostic tools.

    Provides common functionality for executing commands via SSH,
    logging results, and managing command execution state.

    Attributes:
        _ssh: SSH connection for command execution
        _results: Dictionary mapping commands to their results
        _logger: Logger instance for this tool
    """

    def __init__(self, ssh: SshConnection, logger: logging.Logger | None = None):
        """Initialize tool with SSH connection.

        Args:
            ssh: Active SSH connection for command execution
            logger: Optional logger for command execution
        """
        self._ssh = ssh
        self._results: dict[str, CmdResult] = {}

        self._logger = logger or logging.getLogger(LogName.MAIN.value)
        self._exec_logger = logger  # Logger to pass to exec_cmd

    def _exec(
        self,
        cmd: str,
        use_time_cmd: bool = False,
        use_shell: bool = False,
        timeout: int | None = 20,
        logger: logging.Logger | None = None,
    ) -> CmdResult:
        """Execute command and return result.

        Args:
            cmd: CLI command to execute
            use_time_cmd: Wrap command with 'time' for execution timing
            use_shell: Use interactive shell instead of exec_cmd
            timeout: Command timeout in seconds (default: 20)
            logger: Optional logger to pass to connection

        Returns:
            Command result
        """
        log = logger or self._logger

        if not self._ssh.is_connected():
            return self._ssh.get_cr_msg_connection(cmd, LogMsg.EXEC_CMD_FAIL)

        try:
            # Use exec_logger if no logger passed
            exec_log = logger or self._exec_logger
            if use_shell:
                output = self._ssh.exec_shell_cmd(cmd)
                cmd_result = CmdResult(cmd=cmd, stdout=output, stderr="", exec_time=0.0, rcode=0)
            else:
                cmd_result = self._ssh.exec_cmd(
                    cmd, timeout=timeout, use_time_cmd=use_time_cmd, logger=exec_log
                )

            if cmd_result.success:
                log.debug(f"{LogMsg.CMD_EXEC_SUCCESS.value}: '{cmd}'")
            else:
                cmd_result = CmdResult.error(cmd, cmd_result.stderr)
        except (OSError, TimeoutError) as e:
            log.exception(f"Command execution failed: {cmd}")
            cmd_result = CmdResult.error(cmd, str(e))
        except Exception as e:
            log.exception(f"Unexpected error executing command: {cmd}")
            cmd_result = CmdResult.error(cmd, f"Unexpected error: {e}")

        self._results[cmd] = cmd_result
        return cmd_result

    def _gen_cmds(self, interface: str, cmd: list[Any]) -> str:
        """Generate command string from template.

        Args:
            interface: Network interface name
            cmd: Command template

        Returns:
            Formatted command
        """
        cmd_mod = []
        for part in cmd:
            match part:
                case CmdInputType.INTERFACE:
                    cmd_mod.append(interface)
                case CmdInputType.MST_PCICONF:
                    cmd_mod.append(helper.get_mst_device(self._ssh, interface))
                case CmdInputType.PCI_ID:
                    cmd_mod.append(helper.get_pci_id(self._ssh, interface))
                case _:
                    cmd_mod.append(part)

        return " ".join(cmd_mod)

    def _log(self, logger: logging.Logger) -> None:
        """Log command execution results.

        Args:
            logger: Logger instance
        """
        for cmd, result in self._results.items():
            if result.success:
                frame = PrettyFrame().build(f"'{cmd}' -> SUCCESS", [])
                logger.info(frame)
                logger.info(f"\n{result.stdout}\n")
            else:
                frame = PrettyFrame().build(f"'{cmd}' -> FAILED", [f"Reason: {result.stderr}"])
                logger.warning(frame)

    def _save(self, path: Path) -> None:
        """Export data to JSON file.

        Args:
            path: Output file path
        """
        try:
            with path.open("w") as f:
                json.dump(self._summarize(), f, indent=2)
        except Exception:
            self._logger.exception("%s%s", LogMsg.STORE_FAIL.value, path)

    def _chk_resp(self, interface: str, resp: dict[str, Any], cr: CmdResult) -> None:
        """Check command result and update response.

        Args:
            interface: Network interface name
            resp: Response dictionary
            cr: Command result
        """
        if cr.success:
            resp[interface] = cr.stdout
        else:
            resp[interface] = CmdResult.error(cr.cmd, cr.stderr, cr.rcode)
