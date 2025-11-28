#!/usr/bin/env python3
"""Utility methods for retrieving commonly used network information."""

import logging

from src.core.connect import SshConnection
from src.core.parser import SutMstStatusVersionParser
from src.core.result import CmdResult
from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.MAIN.value)


def get_pci_id(ssh: SshConnection, interface: str) -> str | None:
    """Get PCI device ID for network interface.

    Args:
        ssh: SSH connection for command execution
        interface: Network interface name

    Returns:
        str | None: PCI device ID or None if failed
    """
    command = f"basename $(readlink -f /sys/class/net/{interface}/device)"
    result = _execute(ssh, command)
    if result.success:
        return ":".join(result.stdout.split(":")[1:]).strip()
    logger.warning(f"Failed to get pci id: {result.stderr}")
    return None


def get_mst_device(ssh: SshConnection, interface: str) -> str | None:
    """Get MST device path for network interface.

    Starts MST service and queries device mapping for the given interface.

    Args:
        ssh: SSH connection for command execution
        interface: Network interface name

    Returns:
        str | None: MST device path or None if failed
    """
    command = "mst start"
    result = _execute(ssh, command)
    if result.success:
        logger.debug("MST started")
    else:
        logger.error("Failed to start MST")
        return None

    command = "mst status -v"
    result = _execute(ssh, command)
    if result.success:
        parser = SutMstStatusVersionParser()
        parser.parse(result.stdout)
        return parser.get_mst_by_pci(get_pci_id(ssh, interface))
    logger.warning(f"Failed to get mst device: {result.stderr}")
    return None


def _execute(ssh: SshConnection, cmd: str) -> CmdResult:
    """Execute command with error handling.

    Args:
        ssh: SSH connection for command execution
        cmd: Command to execute

    Returns:
        CmdResult: Command execution result
    """
    result = None
    try:
        if not ssh.is_connected():
            message = f"Cannot execute command '{cmd}': No SSH connection"
            logger.error(message)
            result = CmdResult.error(cmd, message)
        else:
            result = ssh.exec_cmd(cmd)
            if result.success:
                logger.debug(f"Successfully executed command: {cmd}")
            else:
                result = CmdResult.error(cmd, result.stderr)
    except Exception as e:
        result = CmdResult.error(cmd, e)

    return result
