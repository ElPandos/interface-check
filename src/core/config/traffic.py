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
    client_server_ips: list[str]
    server_server_ips: list[str]
    client_start_port: int
    server_connect_type: str
    client_host: str
    client_user: str
    client_pass: str
    client_sudo_pass: str
    client_connect_type: str
    setup_traffic_duration_sec: int
    setup_protocol: str
    setup_bandwidth: str
    setup_parallel_streams: int
    setup_stats_poll_sec: int
    web_enabled: bool
    web_port: int

    @classmethod
    def from_dict(cls, data: dict) -> "TrafficConfig":
        """Create TrafficConfig from JSON dict.

        Args:
            data: Configuration dictionary with jump, server, client, test sections

        Returns:
            TrafficConfig instance
        """
        j, srv, cli, test = data["jump"], data["server"], data["client"], data["setup"]
        web = data.get("web", {})
        return cls(
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            server_host=srv["host"],
            server_user=srv["user"],
            server_pass=srv["pass"],
            server_sudo_pass=srv.get("sudo_pass", ""),
            client_server_ips=cli.get("server_ip", [srv["host"]]),
            server_server_ips=srv.get("server_ip", []),
            client_start_port=test.get("start_port", 5001),
            server_connect_type=srv.get("connect_type", ConnectType.REMOTE.value),
            client_host=cli["host"],
            client_user=cli["user"],
            client_pass=cli["pass"],
            client_sudo_pass=cli.get("sudo_pass", ""),
            client_connect_type=cli.get("connect_type", ConnectType.REMOTE.value),
            setup_traffic_duration_sec=test.get(
                "traffic_duration_sec", test.get("it_duration_sec", test.get("duration_sec", 30))
            ),
            setup_protocol=test.get("protocol", "tcp"),
            setup_bandwidth=test.get("bandwidth", "10G"),
            setup_parallel_streams=test.get("parallel_streams", 1),
            setup_stats_poll_sec=test.get("stats_poll_sec", test.get("interval_sec", 1)),
            web_enabled=web.get("enabled", False),
            web_port=web.get("port", 8080),
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
        if not self.client_host:
            errors.append("client_host cannot be empty")
        if not self.client_server_ips:
            errors.append("client_server_ips cannot be empty")
        if self.server_server_ips and len(self.server_server_ips) != len(self.client_server_ips):
            errors.append(
                f"server_server_ips length ({len(self.server_server_ips)}) "
                f"must match client_server_ips length ({len(self.client_server_ips)})"
            )
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
        if self.setup_traffic_duration_sec < 0:
            errors.append(
                f"Invalid traffic_duration_sec: {self.setup_traffic_duration_sec} (must be >= 0, 0 = infinite)"
            )
        if self.setup_protocol not in ["tcp", "udp"]:
            errors.append(f"Invalid protocol: {self.setup_protocol} (must be tcp or udp)")
        if self.setup_parallel_streams < 1:
            errors.append(f"Invalid parallel streams: {self.setup_parallel_streams} (must be >= 1)")
        if self.setup_stats_poll_sec < 0:
            errors.append(f"Invalid stats_poll_sec: {self.setup_stats_poll_sec} (must be >= 0)")
        if self.client_start_port < 1 or self.client_start_port > 65535:
            errors.append(f"Invalid port: {self.client_start_port} (must be 1-65535)")

        if errors:
            logger.error(f"{LogMsg.CONFIG_VALIDATION_FAILED.value}:")
            for error in errors:
                logger.error(f"  - {error}")
            return False

        logger.info(LogMsg.CONFIG_VALIDATION_SUCCESS.value)
        return True
