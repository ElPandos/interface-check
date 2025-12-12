"""Configuration for main_scan_traffic.py - Iperf traffic testing."""

from dataclasses import dataclass

from src.core.enum.connect import ConnectType
from src.core.enum.messages import LogMsg


@dataclass(frozen=True)
class TrafficConfig:
    """Traffic test configuration.

    Contains all settings for:
    - Jump host connection
    - Server and client host connections
    - Iperf test parameters
    """

    log_level: str
    jump_host: str
    jump_user: str
    jump_pass: str
    server_host: str
    server_user: str
    server_pass: str
    server_sudo_pass: str
    server_ip: str
    server_port: int
    server_connect_type: str
    client_host: str
    client_user: str
    client_pass: str
    client_sudo_pass: str
    client_connect_type: str
    test_duration_sec: int
    test_protocol: str
    test_bandwidth: str
    test_parallel_streams: int
    test_interval_sec: int
    test_iterations: int
    test_delay_between_tests_sec: int

    @classmethod
    def from_dict(cls, data: dict) -> "TrafficConfig":
        """Create TrafficConfig from JSON dict.

        Args:
            data: Configuration dictionary with jump, server, client, test sections

        Returns:
            TrafficConfig instance
        """
        j, srv, cli, test = data["jump"], data["server"], data["client"], data["test"]
        return cls(
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            server_host=srv["host"],
            server_user=srv["user"],
            server_pass=srv["pass"],
            server_sudo_pass=srv.get("sudo_pass", ""),
            server_ip=test.get("server_ip", srv["host"]),
            server_port=test.get("port", 5001),
            server_connect_type=srv.get("connect_type", ConnectType.REMOTE.value),
            client_host=cli["host"],
            client_user=cli["user"],
            client_pass=cli["pass"],
            client_sudo_pass=cli.get("sudo_pass", ""),
            client_connect_type=cli.get("connect_type", ConnectType.REMOTE.value),
            test_duration_sec=test.get("duration_sec", 30),
            test_protocol=test.get("protocol", "tcp"),
            test_bandwidth=test.get("bandwidth", "10G"),
            test_parallel_streams=test.get("parallel_streams", 1),
            test_interval_sec=test.get("interval_sec", 1),
            test_iterations=test.get("iterations", 5),
            test_delay_between_tests_sec=test.get("delay_between_tests_sec", 5),
        )

    def validate(self, logger) -> bool:
        """Validate configuration values.

        Args:
            logger: Logger instance for error messages

        Returns:
            bool: True if valid, False otherwise
        """
        errors = []

        if not self.server_host:
            errors.append("server_host cannot be empty")
        if not self.server_ip:
            errors.append("server_ip cannot be empty")
        if not self.client_host:
            errors.append("client_host cannot be empty")
        valid_types = [t.value for t in ConnectType]
        if self.server_connect_type not in valid_types:
            errors.append(
                f"Invalid server_connect_type: {self.server_connect_type} (must be {' or '.join(valid_types)})"
            )
        if self.client_connect_type not in valid_types:
            errors.append(
                f"Invalid client_connect_type: {self.client_connect_type} (must be {' or '.join(valid_types)})"
            )
        if self.test_duration_sec <= 0:
            errors.append(f"Invalid duration: {self.test_duration_sec} (must be >= 1)")
        if self.test_protocol not in ["tcp", "udp"]:
            errors.append(f"Invalid protocol: {self.test_protocol} (must be tcp or udp)")
        if self.test_parallel_streams < 1:
            errors.append(f"Invalid parallel streams: {self.test_parallel_streams} (must be >= 1)")
        if self.test_interval_sec <= 0:
            errors.append(f"Invalid interval: {self.test_interval_sec} (must be > 0)")
        if self.test_iterations < 0:
            errors.append(
                f"Invalid iterations: {self.test_iterations} (must be >= 0, 0 will use infinite traffic)"
            )
        if self.test_delay_between_tests_sec < 0:
            errors.append(f"Invalid delay: {self.test_delay_between_tests_sec} (must be >= 0)")
        if self.server_port < 1 or self.server_port > 65535:
            errors.append(f"Invalid port: {self.server_port} (must be 1-65535)")

        if errors:
            logger.error(f"{LogMsg.CONFIG_VALIDATION_FAILED.value}:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info(LogMsg.CONFIG_VALIDATION_SUCCESS.value)
        return True
