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
        server_host: str,
        port: int = 5001,
    ):
        """Initialize iperf client.

        Args:
            connection: Connection instance
            logger: Logger instance
            server_host: Server IP address
            port: Server port (default: 5201)
        """
        super().__init__(connection, logger)
        self._server_host = server_host
        self._port = port
        self._duration = 10
        self._protocol = "tcp"
        self._bandwidth = None
        self._parallel = 1
        self._use_json = False
        self._timeout_sec = None
        self._interval = 1

    def configure(
        self,
        duration: int = 10,
        protocol: str = "tcp",
        bandwidth: str | None = None,
        parallel: int = 1,
        use_json: bool = False,
        timeout_sec: int | None = None,
        interval: int = 1,
    ) -> None:
        """Configure client parameters.

        Args:
            duration: Test duration in seconds (default: 10, 0 for infinite)
            protocol: Protocol tcp/udp (default: tcp)
            bandwidth: Target bandwidth for UDP (e.g., "1G", "100M")
            parallel: Number of parallel streams (default: 1)
            use_json: Use JSON output format (default: False)
            timeout_sec: Test abort timeout in seconds (default: None, ignored if infinite=True)
            interval: Reporting interval in seconds (default: 1)
        """
        self._duration = duration
        self._protocol = protocol.lower()
        self._bandwidth = bandwidth
        self._parallel = parallel
        self._use_json = use_json
        self._timeout_sec = None if self._duration == 0 else (timeout_sec or duration + 30)
        self._interval = interval
        self._logger.debug(
            f"Configured: duration={self._duration}s{'(infinite)' if self._duration == 0 else ''}, protocol={protocol}, "
            f"bandwidth={bandwidth}, parallel={parallel}, json={use_json}, "
            f"interval={interval}s"
        )

    def start(self, retry_count: int = 0) -> bool:
        """Start iperf client test.

        Note: Client runs in blocking mode (foreground) and waits for test completion.
        No PID tracking needed unlike server daemon mode.

        Args:
            retry_count: Number of retries attempted (internal use)

        Returns:
            True if test completed successfully
        """
        if not self.ensure_required_sw(skip_check=True):
            self._logger.error("Cannot start client: required software not available")
            return False

        self._cleanup_existing_processes()

        cmd = (
            f"iperf -c {self._server_host} -p {self._port} -t {self._duration} "
            f"-P {self._parallel} -i {self._interval}"
        )

        if self._protocol == "udp":
            cmd += " -u"
            if self._bandwidth:
                cmd += f" -b {self._bandwidth}"

        if self._use_json:
            cmd += " -J"

        self._logger.info(f"Starting iperf client: {cmd}")
        result = self._conn.exec_cmd(cmd, timeout=self._timeout_sec)  # Blocking call

        if result.rcode != 0:
            self._logger.error(f"Client test failed: {result.stderr}")
            if retry_count < 2 and "Connection refused" in result.stderr:
                self._logger.warning(f"Retrying test (attempt {retry_count + 2}/3)...")
                time.sleep(2)
                return self.start(retry_count=retry_count + 1)
            return False

        # Parse output from completed test
        self._stats = self._parse_output(result.stdout, use_json=self._use_json)
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
