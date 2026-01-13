"""Iperf client manager."""

import logging
import time

from src.core.traffic.iperf.base import IperfBase
from src.interfaces.component import IConnection


class IperfClient(IperfBase):
    """Iperf client manager."""

    def __init__(
        self,
        connection: IConnection,
        logger: logging.Logger,
        port: int = 5001,
        server_host: str | None = None,
    ):
        """Initialize iperf client.

        Args:
            connection: Connection instance
            logger: Logger instance
            port: Server port (default: 5001)
            server_host: Server IP address
        """
        super().__init__(connection, logger)
        self._server_host = server_host
        self._port = port
        self._duration = 10
        self._protocol = "tcp"
        self._bandwidth = None
        self._parallel = 1
        self._timeout_sec = None
        self._interval = 1
        self._log_dir = self.DEFAULT_LOG_DIR

    def configure(
        self,
        duration: int = 10,
        protocol: str = "tcp",
        bandwidth: str | None = None,
        parallel: int = 1,
        timeout_sec: int | None = None,
        interval: int = 1,
    ) -> None:
        """Configure client parameters.

        Args:
            duration: Test duration in seconds (default: 10, 0 for infinite)
            protocol: Protocol tcp/udp (default: tcp)
            bandwidth: Target bandwidth for UDP (e.g., "1G", "100M")
            parallel: Number of parallel streams (default: 1)
            timeout_sec: Test abort timeout in seconds (default: None, ignored if infinite=True)
            interval: Reporting interval in seconds (default: 1)
        """
        self._duration = duration
        self._protocol = protocol.lower()
        self._bandwidth = bandwidth
        self._parallel = parallel
        self._timeout_sec = None if duration == 0 else (timeout_sec or duration + 30)
        self._interval = interval
        self._logger.debug(
            f"Configured: duration={self._duration}s{'(infinite)' if self._duration == 0 else ''}, protocol={protocol}, "
            f"bandwidth={bandwidth}, parallel={parallel}, "
            f"interval={interval}s"
        )

    def start(self, retry_count: int = 0) -> bool:
        """Start iperf client test.

        Args:
            retry_count: Number of retries attempted (internal use)

        Returns:
            True if test started/completed successfully
        """
        if not self.ensure_required_sw(skip_check=True):
            self._logger.error("Cannot start client: required software not available")
            return False

        # Log file name
        log_file = f"{self._log_dir}/iperf_client_{self._server_host}_{self._port}.log"

        self._cleanup_log_file(log_file)

        cmd = (
            f"iperf -c {self._server_host} -p {self._port} -t {self._duration} "
            f"-P {self._parallel} -i {max(0, self._interval)}"
        )

        if self._protocol == "udp":
            cmd += " -u"
            if self._bandwidth:
                cmd += f" -b {self._bandwidth}"

        self._logger.info(f"Starting iperf client to {self._server_host}:{self._port}")

        # For infinite duration, run in background
        if self._duration == 0:
            bg_cmd = f"nohup {cmd} > {log_file} 2>&1 &"
            result = self._conn.exec_cmd(bg_cmd, timeout=5)
            if result.rcode == 0:
                self._logger.info("Client started in background")
                return True
            self._logger.error(f"Failed to start background client (rcode={result.rcode})")
            return False

        # For finite duration, run blocking
        result = self._conn.exec_cmd(cmd, timeout=self._timeout_sec)

        self._logger.debug(f"Client return code: {result.rcode}")
        self._logger.debug(f"Client stdout length: {len(result.stdout)}")
        if result.stdout:
            self._logger.debug(f"Client stdout: {result.stdout[:500]}")
        if result.stderr:
            self._logger.debug(f"Client stderr: {result.stderr[:500]}")

        # Check for connection errors only if stdout doesn't show successful connection
        if "Connection refused" in result.stderr or "connect failed" in result.stderr:
            if "connected with" not in result.stdout:
                self._logger.error(f"Connection failed to {self._server_host}:{self._port}")
                if retry_count < 2:
                    self._logger.warning(f"Retrying test (attempt {retry_count + 2}/3)...")
                    time.sleep(2)
                    return self.start(retry_count=retry_count + 1)
                return False
            self._logger.debug("Connection errors in stderr but stdout shows successful connections - continuing")

        if result.rcode != 0:
            self._logger.error(f"Client test failed (rcode={result.rcode}): {result.stderr}")
            return False

        # Parse output from completed test
        if not result.stdout or not result.stdout.strip() or "connected with" not in result.stdout:
            self._logger.error("No output from iperf client - connection likely failed")
            self._logger.error(f"Stderr: {result.stderr}")
            return False

        self._stats = self._parse_output(result.stdout, use_json=False)
        self._logger.info(f"Test completed, collected {len(self._stats)} samples")

        # Validate results
        is_valid, error_msg = self.validate_results(self._stats)
        if not is_valid:
            self._logger.error(f"Results validation failed: {error_msg}")
            return False

        # Log summary
        summary = self.get_stats_summary()
        if summary:
            self._logger.info(
                f"Summary: avg={summary['bandwidth_avg_bps'] / 1e9:.2f}Gbps, "
                f"min={summary['bandwidth_min_bps'] / 1e9:.2f}Gbps, "
                f"max={summary['bandwidth_max_bps'] / 1e9:.2f}Gbps"
            )

        return True

    @staticmethod
    def validate_pair(
        server,
        client: "IperfClient",
        server_ip: str,
        port: int,
        logger: logging.Logger,
    ) -> bool:
        """Validate server/client pair connectivity.

        Args:
            server: Server instance
            client: Client instance
            server_ip: Server IP
            port: Port number
            logger: Logger instance

        Returns:
            True if validation successful
        """
        if not server.validate_connection():
            logger.error(f"Server validation failed on port {port}")
            return False

        if not client.validate_connection(server_ip):
            logger.error(f"Client validation failed for {server_ip}")
            return False

        return True
