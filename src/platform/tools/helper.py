#!/usr/bin/env python3
"""
Utility methods for retrieving common used network indormation.
"""

import logging

from src.core.connect import SshConnection
from src.core.parser import MstStatusVersionParser
from src.interfaces.connection import CmdResult
from src.platform.enums.log import LogName

_logger = logging.getLogger(LogName.MAIN.value)


def get_pci_id(ssh_connection: SshConnection, interface: str) -> str | None:
    command = f"basename $(readlink -f /sys/class/net/{interface}/device)"
    result = _execute(ssh_connection, command)
    if result.success:
        return ":".join(result._stdout.split(":")[1:]).strip()
    _logger.warning(f"Failed to get pci id: {result._stderr}")
    return None


def get_mst_device(ssh_connection: SshConnection, interface: str) -> str | None:
    command = "sudo mst status -v"
    result = _execute(ssh_connection, command)
    if result.success:
        parser = MstStatusVersionParser(result._stdout)
        return parser.get_mst_by_pci(get_pci_id(ssh_connection, interface))
    _logger.warning(f"Failed to get mst device: {result._stderr}")
    return None


def _execute(ssh_connection: SshConnection, command: str) -> CmdResult:
    result = None
    try:
        if not ssh_connection.is_connected():
            message = f"Cannot execute command '{command}': No SSH connection"
            _logger.error(message)
            result = CmdResult.error(command, message)
        else:
            result = ssh_connection.exec_cmd(command)
            if result.success:
                _logger.debug(f"Succesfully executed command: {command}")
            else:
                result = CmdResult.error(command, result._stderr)
    except Exception as e:
        result = CmdResult.error(command, e)

    return result
