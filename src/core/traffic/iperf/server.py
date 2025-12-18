"""Iperf server manager."""

import logging

from src.core.enum.messages import LogMsg
from src.core.traffic.iperf.base import IperfBase
from src.interfaces.component import IConnection


class IperfServer(IperfBase):
    """Iperf server manager."""

    def __init__(
        self,
        connection: IConnection,
        logger: logging.Logger,
        port: int = 5201,
        bind_ip: str | None = None,
    ):
        """Initialize iperf server.

        Args:
            connection: Connection instance
            logger: Logger instance
            port: Server port (default: 5201)
            bind_ip: IP address to bind to (default: None = all interfaces)
        """
        super().__init__(connection, logger)
        self._port = port
        self._bind_ip = bind_ip
        self._log_dir = self.DEFAULT_LOG_DIR

    def start(self, skip_checks: bool = False) -> bool:
        """Start iperf server.

        Note: Server runs as daemon (background) and requires PID tracking for lifecycle management.

        Args:
            skip_checks: Skip software and cleanup checks (default: False)

        Returns:
            True if started successfully
        """
        if not skip_checks:
            if not self.ensure_required_sw():
                self._logger.error("Cannot start server: Required software not available")
                return False
            self._cleanup_existing_processes()

        # Log file name
        log_file = f"{self._log_dir}/iperf_server_{self._port}.log"

        self._cleanup_log_file(log_file)

        if not self._check_port_available(self._port):
            self._logger.error(f"Port {self._port} is already in use")
            return False

        cmd = f"iperf -s -p {self._port} -i 1"
        if self._bind_ip:
            cmd += f" -B {self._bind_ip}"

        cmd = f"nohup {cmd} > {log_file} 2>&1 &"

        if not self._exec_cmd(cmd):
            return False

        if not self._get_pid(f"iperf -s.*{self._port}"):
            return False

        return self._verify_port_listening(self._port)

    def start_with_logging(
        self,
        server_ip: str,
        direction: str,
        monitor=None,
    ) -> bool:
        """Start server with logging to monitor.

        Args:
            server_ip: Server IP address
            direction: Direction label (forward/reverse)
            monitor: Optional monitor for logging

        Returns:
            True if started successfully
        """
        msg = f"{LogMsg.TRAFFIC_SERVER_START.value} ({direction} {server_ip}:{self._port})"
        self._logger.info(msg)
        if monitor:
            monitor.log(msg)

        if not self.start(skip_checks=True):
            err_msg = f"{LogMsg.MAIN_SCAN_FAILED_START.value} on port {self._port}"
            self._logger.error(err_msg)
            if monitor:
                monitor.log(err_msg)
            return False
        return True
