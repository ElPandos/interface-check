"""Ethtool CLI tool implementation."""

from dataclasses import dataclass
from typing import Any

from src.mixins.tool import Tool


@dataclass(frozen=True)
class EthtoolInfo:
    """Ethtool interface information."""

    speed: str | None
    duplex: str | None
    link_detected: bool
    auto_negotiation: str | None


@dataclass(frozen=True)
class EthtoolStats:
    """Ethtool statistics."""

    rx_packets: int
    tx_packets: int
    rx_bytes: int
    tx_bytes: int
    rx_errors: int
    tx_errors: int


class EthtoolTool(Tool):
    """Ethtool network interface diagnostic tool."""

    @property
    def tool_name(self) -> str:
        return "ethtool"

    def get_commands(self) -> dict[str, str]:
        """Get available ethtool commands."""
        return {
            "info": "ethtool {interface}",
            "statistics": "ethtool -S {interface}",
            "driver": "ethtool -i {interface}",
            "features": "ethtool -k {interface}",
            "ring": "ethtool -g {interface}",
            "coalesce": "ethtool -c {interface}",
        }

    def parse_output(self, command_name: str, raw_output: str) -> Any:
        """Parse ethtool command output."""
        if command_name == "info":
            return self._parse_info(raw_output)
        if command_name == "statistics":
            return self._parse_statistics(raw_output)
        if command_name == "driver":
            return self._parse_driver_info(raw_output)
        return self._parse_key_value(raw_output)

    def _parse_info(self, output: str) -> EthtoolInfo:
        """Parse ethtool interface info."""
        lines = output.strip().split("\n")
        data = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        return EthtoolInfo(
            speed=data.get("Speed"),
            duplex=data.get("Duplex"),
            link_detected=data.get("Link detected", "").lower() == "yes",
            auto_negotiation=data.get("Auto-negotiation"),
        )

    def _parse_statistics(self, output: str) -> EthtoolStats:
        """Parse ethtool statistics."""
        lines = output.strip().split("\n")[1:]  # Skip header
        stats = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                try:
                    stats[key.strip()] = int(value.strip())
                except ValueError:
                    stats[key.strip()] = value.strip()

        return EthtoolStats(
            rx_packets=stats.get("rx_packets", 0),
            tx_packets=stats.get("tx_packets", 0),
            rx_bytes=stats.get("rx_bytes", 0),
            tx_bytes=stats.get("tx_bytes", 0),
            rx_errors=stats.get("rx_errors", 0),
            tx_errors=stats.get("tx_errors", 0),
        )

    def _parse_driver_info(self, output: str) -> dict[str, str]:
        """Parse driver information."""
        return self._parse_key_value(output)

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse generic key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result
