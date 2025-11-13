"""Validation utilities for improved data integrity."""

import re
from typing import Any

from src.core.base import Result, Validator


class NetworkValidator(Validator[str]):
    """Network-related validation."""

    IP_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    def validate(self, ip: str) -> Result[None]:
        """Validate IP address.

        Args:
            ip: IP address string

        Returns:
            Validation result
        """
        if not isinstance(ip, str):
            return Result.fail("IP must be string")

        if not self.IP_PATTERN.match(ip.strip()):
            return Result.fail("Invalid IP address format")

        return Result.ok(None)


class InputValidator(Validator[str]):
    """Input validation for security."""

    def __init__(self, max_length: int = 255, allow_empty: bool = False):
        """Initialize validator.

        Args:
            max_length: Maximum string length
            allow_empty: Allow empty strings
        """
        self.max_length = max_length
        self.allow_empty = allow_empty

    def validate(self, data: str) -> Result[None]:
        """Validate input string.

        Args:
            data: Input string

        Returns:
            Validation result
        """
        if not isinstance(data, str):
            return Result.fail("Input must be string")

        if not self.allow_empty and not data.strip():
            return Result.fail("Input cannot be empty")

        if len(data) > self.max_length:
            return Result.fail(f"Input too long (max {self.max_length})")

        # Check for potential injection patterns
        dangerous_patterns = ["<script", "<?php", "${", "$(", "`"]
        data_lower = data.lower()
        for pattern in dangerous_patterns:
            if pattern in data_lower:
                return Result.fail("Input contains potentially dangerous content")

        return Result.ok(None)


class ConfigValidator(Validator[dict[str, Any]]):
    """Configuration validation."""

    def __init__(self, required_keys: list[str] | None = None):
        """Initialize validator.

        Args:
            required_keys: List of required keys
        """
        self.required_keys = required_keys or []

    def validate(self, config: dict[str, Any]) -> Result[None]:
        """Validate configuration dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            Validation result
        """
        if not isinstance(config, dict):
            return Result.fail("Config must be dictionary")

        # Check required keys
        for key in self.required_keys:
            if key not in config:
                return Result.fail(f"Missing required key: {key}")

        return Result.ok(None)


class HostValidator(Validator[dict[str, Any]]):
    """Host configuration validation."""

    def __init__(self):
        """Initialize validator."""
        self.ip_validator = NetworkValidator()
        self.input_validator = InputValidator()

    def validate(self, host: dict[str, Any]) -> Result[None]:
        """Validate host configuration.

        Args:
            host: Host configuration dictionary

        Returns:
            Validation result
        """
        if not isinstance(host, dict):
            return Result.fail("Host must be dictionary")

        # Required fields
        required = ["ip", "username", "password"]
        for field in required:
            if field not in host:
                return Result.fail(f"Missing required field: {field}")

        # Validate IP
        ip_result = self.ip_validator.validate(host["ip"])
        if not ip_result.success:
            return ip_result

        # Validate username
        username_result = self.input_validator.validate(host["username"])
        if not username_result.success:
            return Result.fail(f"Invalid username: {username_result.error}")

        # Validate password
        password_result = self.input_validator.validate(host["password"])
        if not password_result.success:
            return Result.fail(f"Invalid password: {password_result.error}")

        return Result.ok(None)


def sanitize_input(value: str, max_length: int = 255) -> str:
    """Sanitize user input.

    Args:
        value: Input string
        max_length: Maximum length

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""

    sanitized = value.strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_ip(ip: str) -> bool:
    """Quick IP validation.

    Args:
        ip: IP address string

    Returns:
        True if valid
    """
    validator = NetworkValidator()
    return validator.validate(ip).success
