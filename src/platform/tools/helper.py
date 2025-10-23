#!/usr/bin/env python3
"""
Utility methods for retrieving common used network indormation.
"""

import logging

logger = logging.getLogger(__name__)


def get_pci_id_command(interface: str) -> str:
    return f"basename $(readlink -f /sys/class/net/{interface}/device)"


def get_mst_device_version_command() -> str:
    return "sudo mst status -v"

    # ssh_connection: SshConnection) -> MstVersionDevice | None:
    # """Execute a mst command and return result.

    # Args:
    #     command: CLI command to execute

    # Returns:
    #     MstDevice with execution details
    # """
    # if not ssh_connection.is_connected():
    #     message = f"Cannot execute command '{command}': No SSH connection"
    #     logger.error(message)
    #     return None

    # command = "sudo mst status -v"
    # result = ssh_connection.execute_command(command)
    # if result.success:
    #     logger.info(f"Succesfully executed command: {command}")
    # else:
    #     return None

    # parser = MstStatusParser(result.stdout)

    # return parser.
