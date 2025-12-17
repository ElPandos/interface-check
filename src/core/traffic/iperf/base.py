"""Iperf base class with common functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import datetime as dt
import json
import logging
import re
import statistics

from src.core.enum.messages import LogMsg
from src.interfaces.component import IConnection


@dataclass
class IperfStats:
    """Iperf statistics data."""

    timestamp: str
    interval: str
    transfer_bytes: float
    bandwidth_bps: float
    jitter_ms: float | None = None
    lost_packets: int | None = None
    total_packets: int | None = None
    loss_percent: float | None = None


class IperfBase(ABC):
    """Base class for iperf server and client."""

    REQUIRED_SW = ["iperf"]

    UNIT_MULTIPLIERS_BYTES = {"K": 1024, "M": 1024**2, "G": 1024**3, "": 1}
    UNIT_MULTIPLIERS_BPS = {"K": 1000, "M": 1000**2, "G": 1000**3, "": 1}

    def __init__(self, connection: IConnection, logger: logging.Logger):
        """Initialize iperf base.

        Args:
            connection: Connection instance (SSH or Local)
            logger: Logger instance
        """
        self._conn = connection
        self._logger = logger
        self._process = None
        self._pid = None
        self._stats: list[IperfStats] = []

    @abstractmethod
    def start(self) -> bool:
        """Start iperf process (must be implemented by subclasses)."""

    def _parse_output(self, output: str, use_json: bool = False) -> list[IperfStats]:
        """Parse iperf output to extract statistics.

        Args:
            output: Raw iperf output (text or JSON)
            use_json: Whether output is JSON format

        Returns:
            List of parsed statistics
        """
        if use_json:
            return self._parse_json_output(output)

        return self._parse_text_output(output)

    def _parse_json_output(self, output: str) -> list[IperfStats]:
        """Parse JSON iperf output.

        Args:
            output: JSON iperf output

        Returns:
            List of parsed statistics
        """
        stats = []
        try:
            data = json.loads(output)
            timestamp = dt.datetime.now().isoformat()

            # Parse intervals from JSON
            for interval in data.get("intervals", []):
                streams = interval.get("streams", [])
                if not streams:
                    continue

                stream = streams[0]  # Use first stream
                stats.append(
                    IperfStats(
                        timestamp=timestamp,
                        interval=f"{interval['sum']['start']}-{interval['sum']['end']}",
                        transfer_bytes=interval["sum"].get("bytes", 0),
                        bandwidth_bps=interval["sum"].get("bits_per_second", 0),
                        jitter_ms=stream.get("jitter_ms"),
                        lost_packets=stream.get("lost_packets"),
                        total_packets=stream.get("packets"),
                        loss_percent=stream.get("lost_percent"),
                    )
                )
        except (json.JSONDecodeError, KeyError) as e:
            self._logger.error(f"{LogMsg.TRAFFIC_JSON_PARSE_FAIL.value}: {e}")

        return stats

    def _parse_text_output(self, output: str) -> list[IperfStats]:
        """Parse text iperf output.

        Args:
            output: Text iperf output

        Returns:
            List of parsed statistics
        """
        stats = []
        timestamp = dt.datetime.now().isoformat()

        # Pattern for bandwidth line: [  3]  0.0- 1.0 sec  1.25 GBytes  10.7 Gbits/sec
        pattern = r"\[\s*\d+\]\s+([\d\.-]+)\s+sec\s+([\d\.]+)\s+([KMG]?)Bytes\s+([\d\.]+)\s+([KMG]?)bits/sec"

        for line in output.splitlines():
            match = re.search(pattern, line)
            if match:
                interval = match.group(1)
                transfer = float(match.group(2))
                transfer_unit = match.group(3)
                bandwidth = float(match.group(4))
                bandwidth_unit = match.group(5)

                # Convert to bytes
                transfer_bytes = self._convert_to_bytes(transfer, transfer_unit)
                bandwidth_bps = self._convert_to_bps(bandwidth, bandwidth_unit)

                # Parse UDP-specific metrics
                jitter = lost = total = loss_pct = None
                jitter_match = re.search(r"([\d\.]+)\s+ms", line)
                if jitter_match:
                    jitter = float(jitter_match.group(1))

                loss_match = re.search(r"(\d+)/\s*(\d+)\s+\(([\d\.]+)%\)", line)
                if loss_match:
                    lost = int(loss_match.group(1))
                    total = int(loss_match.group(2))
                    loss_pct = float(loss_match.group(3))

                stats.append(
                    IperfStats(
                        timestamp=timestamp,
                        interval=interval,
                        transfer_bytes=transfer_bytes,
                        bandwidth_bps=bandwidth_bps,
                        jitter_ms=jitter,
                        lost_packets=lost,
                        total_packets=total,
                        loss_percent=loss_pct,
                    )
                )

        return stats

    def _convert_to_bytes(self, value: float, unit: str) -> float:
        """Convert value to bytes."""
        return value * self.UNIT_MULTIPLIERS_BYTES.get(unit, 1)

    def _convert_to_bps(self, value: float, unit: str) -> float:
        """Convert value to bits per second."""
        return value * self.UNIT_MULTIPLIERS_BPS.get(unit, 1)

    def get_stats(self) -> list[IperfStats]:
        """Get collected statistics.

        Returns:
            List of statistics
        """
        return self._stats

    def get_stats_summary(self) -> dict[str, float] | None:
        """Get summary statistics.

        Returns:
            Dictionary with min/max/avg/stddev or None if no stats
        """
        if not self._stats:
            return None

        bandwidths = [s.bandwidth_bps for s in self._stats]
        transfers = [s.transfer_bytes for s in self._stats]

        return {
            "begin_timestamp": dt.datetime.now(),
            "bandwidth_min_bps": min(bandwidths),
            "bandwidth_max_bps": max(bandwidths),
            "bandwidth_avg_bps": statistics.mean(bandwidths),
            "bandwidth_stddev_bps": statistics.stdev(bandwidths) if len(bandwidths) > 1 else 0,
            "transfer_total_bytes": sum(transfers),
            "sample_count": len(self._stats),
        }

    def is_running(self) -> bool:
        """Check if iperf process is running.

        Returns:
            True if running
        """
        if not self._pid:
            return False

        result = self._conn.exec_cmd(f"ps -p {self._pid}", timeout=5)
        return result.rcode == 0

    def _cleanup_existing_processes(self) -> None:
        """Kill any existing iperf processes."""
        self._logger.info(LogMsg.TRAFFIC_IPERF_CHECK.value)
        result = self._conn.exec_cmd("pkill -9 iperf", timeout=5)
        if result.rcode == 0:
            self._logger.info(LogMsg.TRAFFIC_IPERF_KILLED.value)

    def _check_sw_installed(self, package: str) -> bool:
        """Check if software package is installed.

        Args:
            package: Package name

        Returns:
            True if installed
        """
        result = self._conn.exec_cmd(f"which {package}", timeout=5)
        return result.rcode == 0

    def _install_sw(self, package: str) -> bool:
        """Install software package.

        Args:
            package: Package name

        Returns:
            True if installation successful
        """
        self._logger.info(f"{LogMsg.TRAFFIC_SW_INSTALLING.value} {package}...")

        # Try apt first
        result = self._conn.exec_cmd("which apt-get", timeout=5)
        if result.rcode == 0:
            result = self._conn.exec_cmd(
                f"apt-get update && apt-get install -y {package}", timeout=120
            )
            if result.rcode == 0:
                self._logger.info(f"'{package}' {LogMsg.TRAFFIC_SW_INSTALL_SUCCESS_APT.value}")
                return True
            self._logger.error(
                f"{LogMsg.TRAFFIC_SW_INSTALL_FAIL_APT.value} {package}: {result.stderr}"
            )
            return False

        # Try yum
        result = self._conn.exec_cmd("which yum", timeout=5)
        if result.rcode == 0:
            result = self._conn.exec_cmd(f"yum install -y {package}", timeout=120)
            if result.rcode == 0:
                self._logger.info(f"{package} {LogMsg.TRAFFIC_SW_INSTALL_SUCCESS_YUM.value}")
                return True
            self._logger.error(
                f"{LogMsg.TRAFFIC_SW_INSTALL_FAIL_YUM.value} {package}: {result.stderr}"
            )
            return False

        self._logger.error(LogMsg.TRAFFIC_SW_NO_PKG_MGR.value)
        return False

    def _verify_sw(self, package: str, version_flag: str = "--version") -> bool:
        """Verify software installation and get version.

        Args:
            package: Package name
            version_flag: Flag to get version (default: --version)

        Returns:
            True if package is working
        """
        result = self._conn.exec_cmd(f"{package} {version_flag}", timeout=5)
        if result.rcode == 0:
            version = result.stdout.split()[0] if result.stdout else "unknown"
            self._logger.info(f"{package} {LogMsg.TRAFFIC_SW_VERIFIED.value}: {version}")
            return True
        self._logger.error(f"{package} {LogMsg.TRAFFIC_SW_VERIFY_FAIL.value}")
        return False

    def ensure_required_sw(self, skip_check: bool = False) -> bool:
        """Ensure required software packages are installed.

        Args:
            skip_check: Skip software check (assume already verified)

        Returns:
            True if all packages available
        """
        if skip_check:
            return True

        missing = []

        self._logger.info(LogMsg.TRAFFIC_SW_CHECK.value)
        for package in self.REQUIRED_SW:
            if not self._check_sw_installed(package):
                self._logger.warning(f"{package} {LogMsg.TRAFFIC_SW_MISSING.value}")
                missing.append(package)
            else:
                self._logger.debug(f"{package} is installed")

        if not missing:
            self._logger.info(LogMsg.TRAFFIC_SW_INSTALLED.value)
            return True

        # Install missing packages
        self._logger.info(f"{LogMsg.TRAFFIC_SW_INSTALL_START.value}: {missing}")
        for package in missing:
            if not self._install_sw(package):
                self._logger.error(f"{LogMsg.TRAFFIC_SW_INSTALL_FAIL.value} {package}")
                return False

        # Verify installations
        self._logger.info(LogMsg.TRAFFIC_SW_VERIFY.value)
        for package in self.REQUIRED_SW:
            if not self._check_sw_installed(package):
                self._logger.error(f"{package} {LogMsg.TRAFFIC_SW_VERIFY_FAIL.value}")
                return False

        self._logger.info(LogMsg.TRAFFIC_SW_VERIFY_SUCCESS.value)
        return True

    def _check_port_available(self, port: int) -> bool:
        """Check if port is available.

        Args:
            port: Port number to check

        Returns:
            True if port is available
        """
        result = self._conn.exec_cmd(f"netstat -tuln | grep ':{port} '", timeout=5)
        if result.success:
            self._logger.info(f"{port} {LogMsg.TRAFFIC_PORT_REACHABLE.value}")

        return result.rcode != 0

    def _exec_cmd(self, cmd: str, timeout: int = 10) -> bool:
        """Execute command and check result.

        Args:
            cmd: Command to execute
            timeout: Command timeout

        Returns:
            True if command succeeded
        """
        self._logger.info(f"{LogMsg.TRAFFIC_CMD_EXEC.value}: {cmd}")
        result = self._conn.exec_cmd(cmd, timeout=timeout)
        if result.rcode != 0:
            self._logger.error(f"{LogMsg.TRAFFIC_CMD_FAIL.value}: {result.stderr}")
            return False
        return True

    def validate_connection(self, target_host: str | None = None) -> bool:
        """Validate connection with ping test.

        Args:
            target_host: Target host to ping (None for self-test)

        Returns:
            True if connection valid
        """
        if target_host:
            self._logger.info(f"{LogMsg.TRAFFIC_CONN_VALIDATE.value} to {target_host}...")
            result = self._conn.exec_cmd(f"ping -c 3 -W 2 {target_host}", timeout=10)
            if result.rcode != 0:
                self._logger.error(f"Cannot reach {target_host}: {result.stderr}")
                return False
            self._logger.info(f"{LogMsg.TRAFFIC_CONN_VALIDATED.value} to {target_host}")
        else:
            self._logger.info(LogMsg.TRAFFIC_CONN_VALIDATE_LOCAL.value)
            result = self._conn.exec_cmd("echo test", timeout=5)
            if result.rcode != 0:
                self._logger.error(LogMsg.TRAFFIC_CONN_LOCAL_FAILED.value)
                return False
            self._logger.info(LogMsg.TRAFFIC_CONN_LOCAL_VALIDATED.value)
        return True

    def check_port_reachable(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if port is reachable on remote host.

        Args:
            host: Target host
            port: Target port
            timeout: Connection timeout in seconds

        Returns:
            True if port is reachable
        """
        conn_type = type(self._conn).__name__
        self._logger.info(
            f"{LogMsg.TRAFFIC_PORT_CHECK.value} {port} on {host}... (via {conn_type})"
        )
        self._logger.debug(f"Connection details: {conn_type} checking {host}:{port}")

        # First check if we can reach the host at all
        ping_result = self._conn.exec_cmd(f"ping -c 1 -W 2 {host}", timeout=5)
        if ping_result.rcode != 0:
            self._logger.error(f"Cannot ping {host}: {ping_result.stderr[:200]}")
            self._logger.debug(f"Ping failed - host {host} unreachable from connection")
        else:
            self._logger.debug(f"Ping to {host} successful")

        cmd = f"nc -z -w {timeout} {host} {port}"
        self._logger.debug(f"Port check command: {cmd}")
        self._logger.debug(f"Executing from: {getattr(self._conn, '_host', 'local')}")

        result = self._conn.exec_cmd(cmd, timeout=timeout + 2)

        if result.rcode == 0:
            self._logger.info(f"Port {port} on {host} {LogMsg.TRAFFIC_PORT_REACHABLE.value}")
            return True

        self._logger.error(f"Port {port} on {host} {LogMsg.TRAFFIC_PORT_UNREACHABLE.value}")
        self._logger.error(f"Return code: {result.rcode}")
        self._logger.error(f"Stdout: {result.stdout[:200] if result.stdout else 'empty'}")
        self._logger.error(f"Stderr: {result.stderr[:200] if result.stderr else 'empty'}")
        self._logger.debug(
            f"Port check failed from {getattr(self._conn, '_host', 'local')} to {host}:{port}"
        )
        return False

    def validate_results(self, stats: list[IperfStats]) -> tuple[bool, str]:
        """Validate test results for anomalies.

        Args:
            stats: List of statistics to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not stats:
            return False, "No statistics collected"

        # Check for zero bandwidth
        zero_bw = [s for s in stats if s.bandwidth_bps == 0]
        if zero_bw:
            return False, f"Found {len(zero_bw)} samples with zero bandwidth"

        # Check for excessive packet loss (UDP only)
        if stats[0].loss_percent is not None:
            high_loss = [s for s in stats if s.loss_percent and s.loss_percent > 10]
            if high_loss:
                avg_loss = sum(s.loss_percent for s in high_loss if s.loss_percent) / len(high_loss)
                return False, f"High packet loss detected: {avg_loss:.2f}% avg"

        return True, ""

    def stop(self) -> bool:
        """Stop iperf process gracefully.

        Returns:
            True if stopped successfully
        """
        if not self._pid:
            self._logger.debug(LogMsg.TRAFFIC_PID_NONE.value)
            return True

        self._logger.info(f"{LogMsg.TRAFFIC_PROCESS_STOP.value} (PID {self._pid})")
        result = self._conn.exec_cmd(f"kill {self._pid}", timeout=5)

        if result.rcode == 0:
            self._pid = None
            self._logger.info(LogMsg.TRAFFIC_PROCESS_STOPPED.value)
            return True

        # Process may have already exited - check if it's actually gone
        if "No such process" in result.stderr:
            self._logger.debug(f"Process {self._pid} already terminated")
            self._pid = None
            return True

        self._logger.error(f"{LogMsg.TRAFFIC_PROCESS_STOP_FAIL.value}: {result.stderr}")
        return False

    def kill(self) -> bool:
        """Force kill iperf process.

        Returns:
            True if killed successfully
        """
        if not self._pid:
            return True

        self._logger.warning(f"{LogMsg.TRAFFIC_PROCESS_KILL.value} (PID {self._pid})")
        result = self._conn.exec_cmd(f"kill -9 {self._pid}", timeout=5)
        self._pid = None
        return result.rcode == 0

    def _get_pid(self, pattern: str) -> bool:
        """Get PID of iperf process.

        Args:
            pattern: Pattern to match process (e.g., 'perf3 -s.*5001')

        Returns:
            True if PID found
        """
        result = self._conn.exec_cmd(f"pgrep -f '{pattern}'", timeout=5)
        if result.rcode == 0 and result.stdout.strip():
            self._pid = int(result.stdout.strip().split()[0])
            self._logger.info(f"{LogMsg.TRAFFIC_PROCESS_STARTED.value} {self._pid}")
            return True
        self._logger.error(LogMsg.TRAFFIC_PROCESS_NO_PID.value)
        return False

    @classmethod
    def kill_all_processes(cls, conn: IConnection, logger: logging.Logger) -> None:
        """Kill all iperf processes on a host.

        Args:
            conn: Connection instance
            logger: Logger instance
        """
        logger.info("Cleaning up iperf processes...")
        try:
            conn.exec_cmd("pkill -9 iperf", timeout=5)
        except Exception:
            logger.exception("Failed to cleanup iperf processes")
