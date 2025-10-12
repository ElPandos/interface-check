"""Adapter for existing collector system."""

from typing import Any

from src.core.data_collector import DataSource
from src.interfaces.connection import IConnection
from src.utils.commands import Command


class CommandDataSource(DataSource[dict[str, Any]]):
    """Data source that executes commands via connection."""

    def __init__(self, connection: IConnection, command: Command, name: str):
        self._connection = connection
        self._command = command
        self._name = name

    def collect(self) -> dict[str, Any]:
        """Execute command and return parsed result."""
        if not self._connection.is_connected():
            msg = "Connection not available"
            raise RuntimeError(msg)

        result = self._connection.execute_command(self._command.syntax)
        if not result.success:
            raise RuntimeError(f"Command failed: {result.stderr}")

        # Simple parsing - can be enhanced based on command type
        return {"raw_output": result.stdout, "command": self._command.syntax, "return_code": result.return_code}

    @property
    def name(self) -> str:
        return self._name


class InterfaceDataSource(DataSource[dict[str, Any]]):
    """Data source for network interface information."""

    def __init__(self, connection: IConnection, interface: str):
        self._connection = connection
        self._interface = interface

    def collect(self) -> dict[str, Any]:
        """Collect interface statistics."""
        if not self._connection.is_connected():
            msg = "Connection not available"
            raise RuntimeError(msg)

        # Get basic interface info
        result = self._connection.execute_command(f"cat /sys/class/net/{self._interface}/statistics/rx_bytes")
        rx_bytes = int(result.stdout.strip()) if result.success else 0

        result = self._connection.execute_command(f"cat /sys/class/net/{self._interface}/statistics/tx_bytes")
        tx_bytes = int(result.stdout.strip()) if result.success else 0

        return {"interface": self._interface, "rx_bytes": rx_bytes, "tx_bytes": tx_bytes}

    @property
    def name(self) -> str:
        return f"interface_{self._interface}"
