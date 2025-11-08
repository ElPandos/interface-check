"""Tool interface for CLI-based network diagnostic tools."""

from dataclasses import dataclass
import itertools
import logging
from pathlib import Path
from typing import Any

from src.core import json
from src.core.connect import SshConnection
from src.core.enums.messages import LogMsg
from src.interfaces.connection import CmdResult
from src.platform.enums.log import LogName
from src.platform.enums.software import CommandInputType
from src.platform.tools import helper


@dataclass(frozen=True)
class ToolResult:
    """Tool result of a command execution."""

    def __init__(self, cmd: str, data: Any, error: str, exec_time: float):
        self._cmd = cmd
        self._data = data
        self._error = error
        self._exec_time = exec_time

    @property
    def success(self) -> bool:
        """Indicates whether the tool was executed successfully."""
        return not self._error.strip()


class Tool:
    def __init__(self, ssh_connection: SshConnection):
        self._ssh_connection = ssh_connection
        self._results: dict[str, CmdResult] = {}

        self._logger = logging.getLogger(LogName.MAIN.value)

    def _exec(self, cmd: str) -> CmdResult:
        """Execute a specific command and return the result.

        Args:
            cmd: CLI command to execute
        """
        cmd_result = None
        if not self._ssh_connection.is_connected():
            return self._ssh_connection.get_cr_msg_connection(cmd, LogMsg.EXEC_CMD_FAIL)

        try:
            cmd_result = self._ssh_connection.exec_cmd(cmd)
            if cmd_result.success:
                self._logger.debug(f"Succesfully executed command: {cmd}")
            else:
                cmd_result = CmdResult.error(cmd, cmd_result.str_err)
        except (OSError, TimeoutError) as e:
            cmd_result = CmdResult.error(cmd, str(e))

        self._results[cmd] = cmd_result

        return cmd_result

    def _gen_cmds(self, interf: str, cmd: list[Any]) -> str:
        """Generate command string by replacing placeholders with actual values.

        Args:
            interf: Network interface name
            cmd: Command template with placeholders

        Returns:
            Formatted command string
        """
        cmd_mod = []
        for part in cmd:
            match part:
                case CommandInputType.INTERFACE:
                    cmd_mod.append(interf)
                case CommandInputType.MST_PCICONF:
                    cmd_mod.append(helper.get_mst_device(self._ssh_connection, interf))
                case CommandInputType.PCI_ID:
                    cmd_mod.append(helper.get_pci_id(self._ssh_connection, interf))
                case _:
                    cmd_mod.append(part)

        return " ".join(cmd_mod)

    def _log(self) -> None:
        """Log all command execution results with formatted output."""
        for cmd, result in self._results.items():
            if result.success:
                border = "".join(itertools.repeat("=", len(f"= {cmd}") + 2))
                self._logger.info(border)
                self._logger.info(f"= '{cmd}' -> SUCCESS")
                self._logger.info(border)
                self._logger.info(f"\n\n{result.str_out}")
            else:
                border = "".join(itertools.repeat("=", len(f"= {cmd}") + 2))
                self._logger.warning(border)
                self._logger.warning(f"= '{cmd}' -> FAILED")
                self._logger.warning(f"= Reason: {result.str_err}")
                self._logger.warning(border)

    def _save(self, path: Path) -> None:
        """Export collected data to JSON file.

        Args:
            path: Path to output file
        """
        try:
            with path.open("w") as f:
                json.dump(self._summarize(), f, indent=2)
        except Exception:
            self._logger.exception("%s%s", LogMsg.STORE_FAIL.value, path)

    def _chk_resp(self, interf: str, resp: dict[str, Any], cr: CmdResult) -> None:
        """Check command result and update response dictionary.

        Args:
            interf: Network interface name
            resp: Response dictionary to update
            cr: Command result to check
        """
        if cr.success:
            resp[interf] = cr.str_out
        else:
            resp[interf] = CmdResult.error(cr.cmd, cr.str_err, cr.rcode)
