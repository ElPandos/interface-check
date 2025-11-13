#!/usr/bin/env python3
"""Utility methods for retrieving commonly used network information."""

import logging

from src.core.connect import SshConnection
from src.core.parser import MstStatusVersionParser
from src.interfaces.connection import CmdResult
from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.CORE_MAIN.value)


def get_pci_id(ssh_connection: SshConnection, interface: str) -> str | None:
    """Get PCI device ID for network interface.

    Args:
        ssh_connection: SSH connection for command execution
        interface: Network interface name

    Returns:
        str | None: PCI device ID or None if failed
    """
    command = f"basename $(readlink -f /sys/class/net/{interface}/device)"
    result = _execute(ssh_connection, command)
    if result.success:
        return ":".join(result.stdout.split(":")[1:]).strip()
    logger.warning(f"Failed to get pci id: {result.stderr}")
    return None


def get_mst_device(ssh_connection: SshConnection, interface: str) -> str | None:
    """Get MST device path for network interface.

    Starts MST service and queries device mapping for the given interface.

    Args:
        ssh_connection: SSH connection for command execution
        interface: Network interface name

    Returns:
        str | None: MST device path or None if failed
    """
    command = "mst start"
    result = _execute(ssh_connection, command)
    if result.success:
        logger.debug("MST started")
    else:
        logger.error("Failed to start MST")
        return None

    command = "mst status -v"
    result = _execute(ssh_connection, command)
    if result.success:
        parser = MstStatusVersionParser(result.stdout)
        return parser.get_mst_by_pci(get_pci_id(ssh_connection, interface))
    logger.warning(f"Failed to get mst device: {result.stderr}")
    return None


def _execute(ssh_connection: SshConnection, cmd: str) -> CmdResult:
    """Execute command with error handling.

    Args:
        ssh_connection: SSH connection for command execution
        cmd: Command to execute

    Returns:
        CmdResult: Command execution result
    """
    result = None
    try:
        if not ssh_connection.is_connected():
            message = f"Cannot execute command '{cmd}': No SSH connection"
            logger.error(message)
            result = CmdResult.error(cmd, message)
        else:
            result = ssh_connection.exec_cmd(cmd)
            if result.success:
                logger.debug(f"Successfully executed command: {cmd}")
            else:
                result = CmdResult.error(cmd, result.stderr)
    except Exception as e:
        result = CmdResult.error(cmd, e)

    return result
