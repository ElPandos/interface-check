"""Configuration for main_scan_traffic.py - Iperf traffic testing."""

from dataclasses import dataclass


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
    test_bidir: bool
    test_reverse: bool

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
            server_port=srv.get("port", 5201),
            server_connect_type=srv.get("connect_type", "remote"),
            client_host=cli["host"],
            client_user=cli["user"],
            client_pass=cli["pass"],
            client_sudo_pass=cli.get("sudo_pass", ""),
            client_connect_type=cli.get("connect_type", "remote"),
            test_duration_sec=test.get("duration_sec", 30),
            test_protocol=test.get("protocol", "tcp"),
            test_bandwidth=test.get("bandwidth", "10G"),
            test_parallel_streams=test.get("parallel_streams", 1),
            test_interval_sec=test.get("interval_sec", 1),
            test_iterations=test.get("iterations", 5),
            test_delay_between_tests_sec=test.get("delay_between_tests_sec", 5),
            test_bidir=test.get("bidir", False),
            test_reverse=test.get("reverse", False),
        )

    def validate(self, logger) -> bool:
        """Validate configuration values.

        Args:
            logger: Logger instance for error messages

        Returns:
            bool: True if valid, False otherwise
        """
        errors = []

        if self.test_duration_sec <= 0:
            errors.append(f"Invalid duration: {self.test_duration_sec} (must be > 0)")
        if self.test_protocol not in ["tcp", "udp"]:
            errors.append(f"Invalid protocol: {self.test_protocol} (must be tcp or udp)")
        if self.test_parallel_streams < 1:
            errors.append(f"Invalid parallel streams: {self.test_parallel_streams} (must be >= 1)")
        if self.test_interval_sec <= 0:
            errors.append(f"Invalid interval: {self.test_interval_sec} (must be > 0)")
        if self.test_iterations < 1:
            errors.append(f"Invalid iterations: {self.test_iterations} (must be >= 1)")
        if self.test_bidir and self.test_reverse:
            errors.append("Cannot use both bidir and reverse mode simultaneously")
        if self.server_port < 1 or self.server_port > 65535:
            errors.append(f"Invalid port: {self.server_port} (must be 1-65535)")

        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info("Configuration validated successfully")
        return True
