"""Ethtool CLI tool implementation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any

from src.enums.tools import SoftwareTool
from src.mixins.tool import Tool, ValueCollection


@dataclass(frozen=True)
class EthtoolInfo:
    """Ethtool interface information."""

    speed: str | None = None
    duplex: str | None = None
    link_detected: bool = False
    auto_negotiation: str | None = None


@dataclass(frozen=True)
class EthtoolStats:
    """Ethtool statistics."""

    rx_packets: int = 0
    tx_packets: int = 0
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_errors: int = 0
    tx_errors: int = 0


class EthtoolCommand(Enum):
    """Available ethtool commands."""

    INFO = "info"
    STATISTICS = "statistics"
    DRIVER = "driver"
    MODULE = "module"
    FEATURES = "features"
    RING = "ring"
    COALESCE = "coalesce"


class EthtoolTool(Tool):
    """Ethtool network interface diagnostic tool."""

    @property
    def tool_name(self) -> str:
        return SoftwareTool.ETHTOOL.value

    def available_commands(self) -> dict[str, str]:
        """Get available ethtool commands."""
        return {
            EthtoolCommand.INFO.value: "{EthtoolTool.name} {interface}",
            EthtoolCommand.STATISTICS.value: "ethtool -S {interface}",
            EthtoolCommand.DRIVER.value: "ethtool -i {interface}",
            EthtoolCommand.MODULE.value: "ethtool -m {interface}",
            EthtoolCommand.FEATURES.value: "ethtool -k {interface}",
            EthtoolCommand.RING.value: "ethtool -g {interface}",
            EthtoolCommand.COALESCE.value: "ethtool -c {interface}",
        }

    def parse_output(self, command_name: str, raw_output: str) -> Any:
        """Parse ethtool command output."""
        parser_map = {
            EthtoolCommand.INFO.value: self._parse_info,
            EthtoolCommand.STATISTICS.value: self._parse_statistics,
            EthtoolCommand.DRIVER.value: self._parse_key_value,
            EthtoolCommand.MODULE.value: self._parse_module,
            EthtoolCommand.FEATURES.value: self._parse_features,
            EthtoolCommand.RING.value: self._parse_ring,
            EthtoolCommand.COALESCE.value: self._parse_numeric_key_value,
        }

        parser = parser_map.get(command_name, self._parse_key_value)
        return parser(raw_output)

    def test(self) -> dict[str, Any]:
        """Test ethtool command output."""
        result = self.execute_command(self.available_commands()[EthtoolCommand.MODULE.value])
        return self._parse_module(result.stdout)

    def _parse_info(self, output: str) -> EthtoolInfo:
        """Parse ethtool interface info."""
        data = self._parse_key_value(output)
        return EthtoolInfo(
            speed=data.get("Speed"),
            duplex=data.get("Duplex"),
            link_detected=data.get("Link detected", "").lower() == "yes",
            auto_negotiation=data.get("Auto-negotiation"),
        )

    def _parse_statistics(self, output: str) -> EthtoolStats:
        """Parse ethtool statistics."""
        stats = self._parse_numeric_key_value(output)
        return EthtoolStats(
            rx_packets=stats.get("rx_packets", 0),
            tx_packets=stats.get("tx_packets", 0),
            rx_bytes=stats.get("rx_bytes", 0),
            tx_bytes=stats.get("tx_bytes", 0),
            rx_errors=stats.get("rx_errors", 0),
            tx_errors=stats.get("tx_errors", 0),
        )

    def _parse_module(self, output: str) -> dict[str, Any]:
        """Parse ethtool module info with enhanced SFP/QSFP parsing."""
        data = self._parse_key_value(output)
        parser = ModuleParser()

        # Enhanced parsing for SFP/QSFP modules
        enhanced_data = {}
        for key, value in data.items():
            enhanced_data[key] = parser.parse_value(value)

            # Add normalized keys
            key_lower = key.lower()
            if key_lower == "vendor name":
                enhanced_data["vendor"] = value
            elif key_lower in ["part number", "pn"]:
                enhanced_data["part_number"] = value
            elif key_lower in ["serial number", "sn"]:
                enhanced_data["serial_number"] = value
            elif "wavelength" in key_lower:
                enhanced_data["wavelength_nm"] = parser.extract_wavelength(value)
            elif "media" in key_lower or "type" in key_lower:
                enhanced_data["media_type"] = value

        return enhanced_data

    def _parse_features(self, output: str) -> dict[str, bool]:
        """Parse ethtool features (on/off values)."""
        result = {}
        for line in output.strip().split("\n"):
            match = re.match(r"\s*(\S+):\s*(on|off)", line)
            if match:
                key, value = match.groups()
                result[key] = value.lower() == "on"
        return result

    def _parse_ring(self, output: str) -> dict[str, dict[str, int]]:
        """Parse ethtool ring parameters."""
        result = {}
        current_section = None

        for line in output.strip().split("\n"):
            if line.strip().endswith(":") and not line.startswith(" "):
                current_section = line.strip(":").strip()
                result[current_section] = {}
            elif current_section:
                match = re.match(r"\s*(\S+):\s*(\d+)", line)
                if match:
                    key, value = match.groups()
                    result[current_section][key] = int(value)
        return result

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse generic key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    def _parse_numeric_key_value(self, output: str) -> dict[str, int]:
        """Parse key-value output with numeric values."""
        result = {}
        for line in output.strip().split("\n"):
            match = re.match(r"\s*(\S+):\s*(\d+)", line)
            if match:
                key, value = match.groups()
                result[key] = int(value)
        return result


class ModuleParser:
    """Parser for SFP/QSFP module information."""

    VALUE_UNIT_RE = re.compile(r"([-+]?\d*\.?\d+)\s*(?:degrees\s*)?([°]?[CF]|[a-zA-Z%]+)")

    def parse_value(self, value: str) -> ValueCollection | list[ValueCollection] | str | None:
        """Parse value with units into structured data."""
        matches = list(self.VALUE_UNIT_RE.finditer(value))
        if not matches:
            return value.strip() or None

        parsed = [ValueCollection(value=float(m.group(1)), unit=m.group(2).strip(), raw=m.group(0)) for m in matches]

        if self._is_temp_pair(parsed):
            return sorted(parsed, key=lambda v: "C" not in v.unit)

        return parsed if len(parsed) > 1 else parsed[0]

    def extract_wavelength(self, value: str) -> int | str:
        """Extract wavelength in nanometers."""
        try:
            match = re.search(r"(\d+)", value)
            return int(match.group(1)) if match else value
        except (AttributeError, ValueError):
            return value

    def _is_temp_pair(self, values: list[ValueCollection]) -> bool:
        """Check if values contain both Celsius and Fahrenheit."""
        if len(values) != 2:
            return False
        units = {v.unit.replace("degrees", "").strip() for v in values}
        return "C" in units and "F" in units
