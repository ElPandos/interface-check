"""Iperf server manager."""

import logging

from src.core.traffic.iperf.base import IperfBase
from src.interfaces.component import IConnection


class IperfServer(IperfBase):
    """Iperf server manager."""

    def __init__(self, connection: IConnection, logger: logging.Logger, port: int = 5201):
        """Initialize iperf server.

        Args:
            connection: Connection instance
            logger: Logger instance
            port: Server port (default: 5201)
        """
        super().__init__(connection, logger)
        self._port = port
        self._use_json = False

    def configure(self, use_json: bool = False) -> None:
        """Configure server parameters.

        Args:
            use_json: Use JSON output format
        """
        self._use_json = use_json

    def start(self, daemon: bool = True) -> bool:
        """Start iperf server.

        Note: Server runs as daemon (background) and requires PID tracking for lifecycle management.

        Args:
            daemon: Run as daemon (default: True)

        Returns:
            True if started successfully
        """
        if not self.ensure_required_sw():
            self._logger.error("Cannot start server: required software not available")
            return False

        self._cleanup_existing_processes()

        if not self._check_port_available(self._port):
            self._logger.error(f"Port {self._port} is already in use after cleanup")
            return False

        cmd = f"iperf -s -p {self._port}"
        if daemon:
            cmd += " -D"
        if self._use_json:
            cmd += " -J"

        if not self._exec_cmd(cmd):
            return False

        return self._get_pid(f"iperf -s.*{self._port}")
