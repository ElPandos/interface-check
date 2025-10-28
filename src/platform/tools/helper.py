#!/usr/bin/env python3
"""
Utility methods for retrieving common used network indormation.
"""

import logging

from src.core.connect import SshConnection
from src.core.parser import MstStatusVersionParser
from src.interfaces.connection import CommandResult

logger = logging.getLogger("main")


def get_pci_id(ssh_connection: SshConnection, interface: str) -> str | None:
    command = f"basename $(readlink -f /sys/class/net/{interface}/device)"
    result = _execute(ssh_connection, command)
    if result.success:
        return ":".join(result.stdout.split(":")[1:]).strip()
    logger.warning(f"Failed to get pci id: {result.stderr}")
    return None


def get_mst_device(ssh_connection: SshConnection, interface: str) -> str | None:
    command = "sudo mst status -v"
    result = _execute(ssh_connection, command)
    if result.success:
        parser = MstStatusVersionParser(result.stdout)
        return parser.get_mst_by_pci(get_pci_id(ssh_connection, interface))
    logger.warning(f"Failed to get mst device: {result.stderr}")
    return None


def _execute(ssh_connection: SshConnection, command: str) -> CommandResult:
    result = None
    try:
        if not ssh_connection.is_connected():
            message = f"Cannot execute command '{command}': No SSH connection"
            logger.error(message)
            result = CommandResult.error(command, message)
        else:
            result = ssh_connection.execute_command(command)
            if result.success:
                logger.debug(f"Succesfully executed command: {command}")
            else:
                result = CommandResult.error(command, result.stderr)
    except Exception as e:
        result = CommandResult.error(command, e)

    return result
