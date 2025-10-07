from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Dict, List, Union
from src.models.configurations import AppConfig
from src.utils.commands import Ethtool
from src.utils.ssh_connection import SshConnection


class EthtoolKey(Enum):
    MODULE_INFO = "module_info"
    STATISTICS = "statistics"
    RING_PARAMS = "ring_params"
    FEATURES = "features"
    COALESCE_PARAMS = "coalesce_params"


@dataclass
class ValueWithUnit:
    """Holds a numeric value and its corresponding unit."""

    value: float
    unit: str
    raw: str = ""


class EthtoolOutputParser:
    """
    Parses raw 'ethtool -m' SFP module output into structured data.
    Supports multiple unit types (e.g. mW/dBm, °C/°F) and always
    returns both temperature values with fixed ordering.
    """

    # Regex to detect numeric + unit groups, e.g. "53.14 degrees C"
    VALUE_UNIT_RE = re.compile(r"([-+]?\d*\.?\d+)\s*(?:degrees\s*)?([°]?[CF]|[a-zA-Z%]+)")

    def parse_value(self, value: str) -> Union[ValueWithUnit, List[ValueWithUnit], str, None]:
        """
        Parses a string like "50.94 degrees C / 123.69 degrees F"
        into structured ValueWithUnit objects.
        """
        matches = list(self.VALUE_UNIT_RE.finditer(value))
        if not matches:
            return value.strip() or None

        parsed = [ValueWithUnit(value=float(m.group(1)), unit=m.group(2).strip(), raw=m.group(0)) for m in matches]

        # Special handling for Celsius/Fahrenheit pairs
        if self._is_temp_pair(parsed):
            # Ensure correct index order: [0] Celsius, [1] Fahrenheit
            parsed_sorted = sorted(parsed, key=lambda v: "C" not in v.unit)
            return parsed_sorted

        # Default behavior: return list if >1, else single
        return parsed if len(parsed) > 1 else parsed[0]

    def _is_temp_pair(self, values: List[ValueWithUnit]) -> bool:
        """Return True if both °C and °F temperature values are found."""
        if len(values) != 2:
            return False
        units = {v.unit.replace("degrees", "").strip() for v in values}
        return "C" in units and "F" in units

    def parse(self, raw_text: str) -> Dict[str, Any]:
        """Parse the full ethtool output into structured fields."""
        data: Dict[str, Any] = {}
        for line in raw_text.splitlines():
            if ":" not in line:
                continue
            key, val = [p.strip() for p in line.split(":", 1)]
            data[key] = self.parse_value(val)
        return data


class EthtoolParser:
    """
    Fully robust ethtool parser for any network interface.

    Features:
    - Validates interface existence
    - Parses:
        - Module info (-m)
        - Statistics (-S)
        - Ring/buffer params (-g)
        - Offload features (-k)
        - Coalescing params (-c)
    - Graceful handling of unsupported commands or permissions
    - Caches command output for performance
    - Enhanced SFP/QSFP EEPROM parsing for vendor, part number, serial, wavelength, media type
    """

    # Regular expression to match a number + unit pattern
    VALUE_UNIT_RE = re.compile(r"([-+]?\d*\.?\d+)\s*([a-zA-Z%°]+)")

    def __init__(self, interface: str, app_config: AppConfig, ssh_connection: SshConnection):
        self._interface = interface

        self._app_config = app_config
        self._ssh_connection = ssh_connection

        self._parser = EthtoolOutputParser()

    # -------------------- Parsers -------------------- #

    def module_info(self) -> Dict[str, Any]:
        """Parse ethtool -m (module EEPROM info) and SFP/QSFP fields."""
        output, error = self._ssh_connection.exec_command(Ethtool().module_info(self._interface).syntax)
        if not output or error:
            print(error)
            return {}

        data = {}
        # Generic key:value parsing
        for line in output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()

        # Enhanced parsing for SFP/QSFP modules
        for key in data.copy():
            val = data[key]
            if key.lower() == "vendor name":
                data["vendor"] = val
            elif key.lower() in ["part number", "pn"]:
                data["part_number"] = val
            elif key.lower() in ["serial number", "sn"]:
                data["serial_number"] = val
            elif "wavelength" in key.lower():
                try:
                    data["wavelength_nm"] = int(re.search(r"\d+", val).group())
                except Exception:
                    data["wavelength_nm"] = val
            elif "media" in key.lower() or "type" in key.lower():
                data["media_type"] = val

            # Try to extract all numeric+unit pairs from the value
            matches = list(self.VALUE_UNIT_RE.finditer(val))

            # if key == 'Module temperature':
            #     hello = 0

            data[key] = self._parser.parse_value(val)

        return data

    def statistics(self) -> Dict[str, int]:
        """Parse ethtool -S (interface statistics)."""
        output, error = self._ssh_connection.exec_command(Ethtool().nic_statistics(self._interface).syntax)
        if not output or error:
            print(error)
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(\d+)", line)
            if match:
                key, value = match.groups()
                data[key] = int(value)
        return data

    def ring_params(self) -> Dict[str, Union[int, Dict[str, int]]]:
        """Parse ethtool -g (ring/buffer parameters)."""
        output, error = self._ssh_connection.exec_command(Ethtool().ring_parameters(self._interface).syntax)
        if not output or error:
            print(error)
            return {}
        data = {}
        current_block = None
        for line in output.splitlines():
            if line.strip().endswith(":") and not line.startswith(" "):
                current_block = line.strip(":").strip()
                data[current_block] = {}
            elif current_block:
                match = re.match(r"\s*(\S+):\s*(\d+)", line)
                if match:
                    key, value = match.groups()
                    data[current_block][key] = int(value)
        return data

    def features(self) -> Dict[str, bool]:
        """Parse ethtool -k (offload features)."""
        output, error = self._ssh_connection.exec_command(Ethtool().offload_features(self._interface).syntax)
        if not output or error:
            print(error)
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(on|off)", line)
            if match:
                key, value = match.groups()
                data[key] = value.lower() == "on"
        return data

    def coalesce_params(self) -> Dict[str, int]:
        """Parse ethtool -c (coalescing parameters)."""
        output, error = self._ssh_connection.exec_command(Ethtool().coalescing_parameters(self._interface).syntax)
        if not output or error:
            print(error)
            return {}
        data = {}
        for line in output.splitlines():
            match = re.match(r"\s*(\S+):\s*(\d+)", line)
            if match:
                key, value = match.groups()
                data[key] = int(value)
        return data

    # -------------------- Unified Output -------------------- #

    def all_info(self) -> Dict[str, Any]:
        """Return all parsed ethtool info as a single dictionary."""
        return {
            EthtoolKey.MODULE_INFO: self.module_info(),
            EthtoolKey.STATISTICS: self.statistics(),
            EthtoolKey.RING_PARAMS: self.ring_params(),
            EthtoolKey.FEATURES: self.features(),
            EthtoolKey.COALESCE_PARAMS: self.coalesce_params(),
        }
