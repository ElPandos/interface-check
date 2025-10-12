"""Host input validation utilities."""

import re
from typing import Any

MAX_INPUT_LENGTH = 255


class HostValidator:
    """Validates host-related inputs."""

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """Validate IP address format."""
        pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return bool(re.match(pattern, ip.strip()))

    @staticmethod
    def validate_and_sanitize_input(value: str, max_length: int = MAX_INPUT_LENGTH) -> str:
        """Validate and sanitize user input."""
        if not isinstance(value, str):
            msg = "Input must be string"
            raise TypeError(msg)
        sanitized = value.strip()
        if len(sanitized) > max_length:
            msg = f"Input too long (max {max_length})"
            raise ValueError(msg)
        return sanitized

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize user input safely."""
        try:
            return HostValidator.validate_and_sanitize_input(value)
        except ValueError:
            return ""

    @staticmethod
    def validate_host_data(ip: str, username: str, password: str, existing_hosts: list[dict[str, Any]]) -> str | None:
        """Validate complete host data. Returns error message or None if valid."""
        if not all([ip, username, password]):
            return "All fields are required"

        if not HostValidator.validate_ip(ip):
            return "Invalid IP address format"

        if any(h["ip"] == ip for h in existing_hosts):
            return "IP address already exists"

        return None

    @staticmethod
    def validate_config(config: dict) -> None:
        """Validate configuration structure."""
        if not isinstance(config, dict):
            msg = "Config must be a dictionary"
            raise TypeError(msg)
        if "hosts" in config and not isinstance(config["hosts"], list):
            msg = "Hosts must be a list"
            raise TypeError(msg)
        if "routes" in config and not isinstance(config["routes"], list):
            msg = "Routes must be a list"
            raise TypeError(msg)
