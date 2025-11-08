from dataclasses import dataclass
import logging
import re
from typing import ClassVar

import numpy as np

from src.interfaces.component import IParser
from src.platform.enums.log import LogName

# ---------------------------------------------------------------------------- #
#                                    Common                                    #
# ---------------------------------------------------------------------------- #


class ParsedDevice:
    def __init__(self, log_name: str):
        self._logger = logging.getLogger(log_name)


# ---------------------------------------------------------------------------- #
#                                   EYE scan                                   #
# ---------------------------------------------------------------------------- #


class EyeScanParser(IParser):
    """Parse SLX 'phy diag xeX eyescan' CLI output into structured data."""

    _row_pattern = re.compile(r"^\s*([\-]?\d+)mV\s*:\s*([0-9:\-\+\| ]+)$")

    # Map pattern characters to numeric levels (you can tune this mapping)
    _char_map: ClassVar[dict[str, int]] = {
        " ": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "+": 10,
        "-": 5,
        "|": 8,
        ":": 2,
    }

    def __init__(self, raw_output: str):
        IParser.__init__(self, LogName.SLX_EYE_SCANNER.value)

        self._raw_output = raw_output
        self._rows: list[dict[str, str]] = self._parse()

    def name(self) -> str:
        return "eye_scan"

    def _parse(self) -> list[dict[str, str]]:
        """Extract voltage/pattern rows from CLI output."""
        rows = []
        for line in self._raw_output.splitlines():
            match = self._row_pattern.match(line)
            if match:
                voltage, pattern = match.groups()
                rows.append(
                    {
                        "voltage": int(voltage.strip()),
                        "pattern": pattern.rstrip(),
                    }
                )
        return rows

    def get_result(self) -> tuple[np.ndarray, list[int], list[int]]:
        """
        Convert parsed rows into a numeric 2D matrix for plotting.

        Returns:
            matrix (2D np.ndarray): intensity grid
            voltages (List[int]): Y-axis voltage values
            phase_offsets (List[int]): X-axis phase offset values (-31 to +31)
        """
        voltages = [row["voltage"] for row in self._rows]
        patterns = [row["pattern"] for row in self._rows]

        max_len = max(len(p) for p in patterns)

        # Convert pattern characters → numeric grid
        matrix = np.array(
            [[self._char_map.get(ch, 0) for ch in p.ljust(max_len)] for p in patterns]
        )

        # Create phase offset values from -31 to +31
        phase_offsets = list(range(-31, 32))  # -31 to +31 inclusive

        return matrix, voltages, phase_offsets

    def log(self) -> None:
        """Log parsed eye scan data."""


# ---------------------------------------------------------------------------- #
#                                      MST                                     #
# ---------------------------------------------------------------------------- #


class MstVersionDevice(ParsedDevice):
    """
    Represents a single Mellanox/NVIDIA device entry from `mst status -v`.
    Contains all relevant fields for diagnostics and mapping.
    """

    def __init__(
        self,
        device_type: str,
        mst: str,
        pci: str,
        rdma: str | None,
        net: str | None,
        numa: str | None,
    ):
        ParsedDevice.__init__(self, LogName.MAIN.value)
        self.device_type = device_type
        self.mst = mst
        self.pci = pci
        self.rdma = rdma if rdma != "-" else None
        self.net = net.replace("net-", "") if net and net.startswith("net-") else net
        self.numa = numa if numa != "-" else None

    def log(self) -> str:
        self._logger.info(
            f"MstDevice(device_type={self.device_type!r}, "
            f"mst={self.mst!r}, pci={self.pci!r}, "
            f"rdma={self.rdma!r}, net={self.net!r}, "
            f"numa={self.numa!r})"
        )


class MstStatusVersionParser(IParser):
    """
    Parser for `mst status -v` output.
    Provides a list of MstDevice objects for easy programmatic use.
    """

    def __init__(self, raw_output: str):
        IParser.__init__(self, LogName.MAIN.value)

        self._raw_output = raw_output
        self._devices: list[MstVersionDevice] = []
        self._parse()

    def name(self) -> str:
        return "mst_version"

    def _parse(self) -> None:
        lines = self._raw_output.splitlines()

        # Find header line (starts with DEVICE_TYPE)
        start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith("DEVICE_TYPE"):
                start_idx = i + 1
                break
        if start_idx is None:
            return  # No devices found

        # Parse table rows
        for line in lines[start_idx:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) < 6:
                continue  # skip malformed lines

            # DEVICE_TYPE can contain spaces, so rebuild carefully
            # Assume MST path always starts with "/dev/mst/"
            try:
                mst_index = next(i for i, p in enumerate(parts) if p.startswith("/dev/mst/"))
            except StopIteration:
                continue

            device_type = " ".join(parts[:mst_index])
            mst = parts[mst_index]
            pci = parts[mst_index + 1]
            rdma = parts[mst_index + 2]
            net = parts[mst_index + 3]
            numa = parts[mst_index + 4] if len(parts) > mst_index + 4 else None

            self._devices.append(MstVersionDevice(device_type, mst, pci, rdma, net, numa))

    def get_result(self) -> list[MstVersionDevice]:
        return self._devices

    def get_mst_by_pci(self, pci_id: str) -> str | None:
        """
        Retrieve the MST device path for a given PCI ID.

        Args:
            pci_id (str): PCI address in format '86:00.0'

        Returns:
            str | None: MST device path if found, else None.
        """
        for mst in self._devices:
            if mst.pci == pci_id:
                return mst.mst

        return None

    def log(self) -> None:
        for device in self._devices:
            device.log()


# ---------------------------------------------------------------------------- #
#                                  Ethtool -m                                  #
# ---------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ValueWithUnit:
    """Represents a value with its unit."""

    value: float
    unit: str
    raw: str


class EthtoolModuleDevice(ParsedDevice):
    """Represents parsed ethtool -m module information."""

    def __init__(self, data: dict[str, str]):
        EthtoolModuleDevice.__init__(self, LogName.MAIN.value)

        self._data = data

    @property
    def module_temperature(self) -> list[ValueWithUnit] | None:
        temp_str = self._data.get("Module temperature")
        if temp_str:
            return self._parse_temperature(temp_str)
        return None

    @property
    def laser_bias_current(self) -> ValueWithUnit | None:
        current_str = self._data.get("Laser bias current")
        if current_str:
            return self._parse_single_value(current_str)
        return None

    @property
    def laser_output_power(self) -> list[ValueWithUnit] | None:
        power_str = self._data.get("Laser output power")
        if power_str:
            return self._parse_power(power_str)
        return None

    def _parse_temperature(self, temp_str: str) -> list[ValueWithUnit]:
        """Parse temperature string like '46.11 degrees C / 115.00 degrees F'."""
        pattern = r"([\d.]+)\s*degrees\s*([CF])"
        matches = re.findall(pattern, temp_str)
        return [
            ValueWithUnit(float(val), f"degrees {unit}", f"{val} degrees {unit}")
            for val, unit in matches
        ]

    def _parse_power(self, power_str: str) -> list[ValueWithUnit]:
        """Parse power string like '0.8070 mW / -0.93 dBm'."""
        pattern = r"([\d.-]+)\s*(mW|dBm)"
        matches = re.findall(pattern, power_str)
        return [ValueWithUnit(float(val), unit, f"{val} {unit}") for val, unit in matches]

    def _parse_single_value(self, value_str: str) -> ValueWithUnit | None:
        """Parse single value with unit like '7.294 mA'."""
        pattern = r"([\d.-]+)\s*([a-zA-Z%]+)"
        match = re.search(pattern, value_str)
        if match:
            val, unit = match.groups()
            return ValueWithUnit(float(val), unit, f"{val} {unit}")
        return None


class EthtoolModuleParser(IParser):
    """Parser for `ethtool -m <interface>` output."""

    def __init__(self, raw_output: str):
        IParser.__init__(self, LogName.MAIN.value)

        self._raw_output = raw_output
        self._result: dict[str, str] = {}
        self._parse()

    def name(self) -> str:
        return "ethtool_module"

    def _parse(self) -> None:
        """Parse key-value pairs from ethtool -m output."""
        for line in self._raw_output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                self._result[key.strip()] = value.strip()

    def get_result(self) -> EthtoolModuleDevice:
        """Return parsed module device."""
        return EthtoolModuleDevice(self._result)

    def log(self) -> None:
        """Log parsed data."""
        device = self.get_result()
        self._logger.info(f"Vendor: {device.vendor_name}")
        self._logger.info(f"Part Number: {device.vendor_pn}")
        self._logger.info(f"Serial Number: {device.vendor_sn}")
        if device.module_temperature:
            temps = ", ".join([f"{t.value} {t.unit}" for t in device.module_temperature])
            self._logger.info(f"Temperature: {temps}")


# ---------------------------------------------------------------------------- #
#                                   Mlxlink                                   #
# ---------------------------------------------------------------------------- #


class MlxlinkDevice(ParsedDevice):
    """Represents parsed mlxlink module information."""

    def __init__(self, data: dict[str, str]):
        ParsedDevice.__init__(self, LogName.MAIN.value)

        self._data = data

    @property
    def state(self) -> str | None:
        return self._data.get("State")

    @property
    def speed(self) -> str | None:
        return self._data.get("Speed")

    @property
    def temperature(self) -> ValueWithUnit | None:
        temp_str = self._data.get("Temperature [C]")
        if temp_str:
            return self._parse_temperature_with_range(temp_str)
        return None

    @property
    def voltage(self) -> ValueWithUnit | None:
        voltage_str = self._data.get("Voltage [mV]")
        if voltage_str:
            return self._parse_value_with_range(voltage_str)
        return None

    @property
    def bias_current(self) -> ValueWithUnit | None:
        current_str = self._data.get("Bias Current [mA]")
        if current_str:
            return self._parse_value_with_range(current_str)
        return None

    @property
    def rx_power(self) -> ValueWithUnit | None:
        power_str = self._data.get("Rx Power Current [dBm]")
        if power_str:
            result = self._parse_value_with_range(power_str)
            if result and result.value == -40.0:
                self._logger.debug(f"rx_power is -40.0 - Raw string: '{power_str}'")
                self._logger.debug(f"Full data dict: {self._data}")
            return result
        return None

    @property
    def tx_power(self) -> ValueWithUnit | None:
        power_str = self._data.get("Tx Power Current [dBm]")
        if power_str:
            return self._parse_value_with_range(power_str)
        return None

    @property
    def vendor_name(self) -> str | None:
        return self._data.get("Vendor Name")

    @property
    def vendor_part_number(self) -> str | None:
        return self._data.get("Vendor Part Number")

    @property
    def vendor_serial_number(self) -> str | None:
        return self._data.get("Vendor Serial Number")

    @property
    def time_since_last_clear(self) -> ValueWithUnit | None:
        time_str = self._data.get("Time Since Last Clear [Min]")
        if time_str and time_str != "N/A":
            return self._parse_scientific_value(time_str, "Min")
        return None

    @property
    def effective_physical_errors(self) -> ValueWithUnit | None:
        errors_str = self._data.get("Effective Physical Errors")
        if errors_str and errors_str != "N/A":
            return self._parse_scientific_value(errors_str, "")
        return None

    @property
    def effective_physical_ber(self) -> ValueWithUnit | None:
        ber_str = self._data.get("Effective Physical BER")
        if ber_str and ber_str != "N/A":
            return self._parse_scientific_value(ber_str, "")
        return None

    @property
    def raw_physical_errors_per_lane(self) -> ValueWithUnit | None:
        errors_str = self._data.get("Raw Physical Errors Per Lane")
        if errors_str and errors_str != "N/A":
            return self._parse_scientific_value(errors_str, "")
        return None

    @property
    def raw_physical_ber(self) -> ValueWithUnit | None:
        ber_str = self._data.get("Raw Physical BER")
        if ber_str and ber_str != "N/A":
            return self._parse_scientific_value(ber_str, "")
        return None

    def _parse_temperature_with_range(self, temp_str: str) -> ValueWithUnit | None:
        """Parse temperature like '50 [-5..75]'."""
        pattern = r"([\d.-]+)"
        match = re.search(pattern, temp_str)
        if match:
            return ValueWithUnit(float(match.group(1)), "C", temp_str)
        return None

    def _parse_value_with_range(self, value_str: str) -> ValueWithUnit | None:
        """Parse value with range like '3317.5 [3000..3600]'."""
        pattern = r"([\d.-]+)"
        match = re.search(pattern, value_str)
        if match:
            # Extract unit from the key (e.g., "mV" from "Voltage [mV]")
            unit_match = re.search(r"\[([a-zA-Z]+)\]", value_str)
            unit = unit_match.group(1) if unit_match else ""
            parsed_value = float(match.group(1))
            if parsed_value == -40.0:
                self._logger.debug(
                    f"Parsed -40.0 from value_str: '{value_str}', matched: '{match.group(1)}'"
                )
            return ValueWithUnit(parsed_value, unit, value_str)
        return None

    def _parse_scientific_value(self, value_str: str, unit: str) -> ValueWithUnit | None:
        """Parse scientific notation values like '15E-255'."""
        pattern = r"([\d.-]+[Ee][+-]?\d+|[\d.-]+)"
        match = re.search(pattern, value_str)
        if match:
            try:
                return ValueWithUnit(float(match.group(1)), unit, value_str)
            except ValueError:
                return None
        return None


class MlxlinkParser(IParser):
    """Parser for command output.
    Command: `mlxlink -d <device> -e -m -c`
    """

    def __init__(self, raw_output: str):
        IParser.__init__(self, LogName.MAIN.value)
        self._raw_output = raw_output

        self._result: dict[str, str] = {}
        self._parse()

    @property
    def name(self) -> str:
        return "mlxlink"

    def _parse(self) -> None:
        """Parse key-value pairs from mlxlink output."""
        if self._raw_output is not None:
            for line in self._raw_output.splitlines():
                if ":" in line and not line.strip().endswith(":"):
                    key, value = line.split(":", 1)
                    if value.strip() == "-40.0":
                        a = ""
                    self._result[key.strip()] = value.strip()

    def get_result(self) -> MlxlinkDevice:
        """Return parsed mlxlink device."""
        return MlxlinkDevice(self._result)

    def log(self) -> None:
        """Log parsed data."""
        device = self.get_result()
        self._logger.info(f"State: {device.state}")
        self._logger.info(f"Speed: {device.speed}")
        self._logger.info(f"Vendor: {device.vendor_name}")
        if device.temperature:
            self._logger.info(f"Temperature: {device.temperature.value} {device.temperature.unit}")
        if device.voltage:
            self._logger.info(f"Voltage: {device.voltage.value} {device.voltage.unit}")


# ---------------------------------------------------------------------------- #
#                           Dmesg - Link flap farser                           #
# ---------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LinkEvent:
    """Represents a single link state change event."""

    timestamp: str
    state: str  # "Up" or "Down"
    interface: str


class LinkFlapDevice(ParsedDevice):
    """Represents link flap statistics for a single network interface."""

    def __init__(self, interface: str, events: list[LinkEvent]):
        ParsedDevice.__init__(self, LogName.MAIN.value)

        self._interface = interface
        self._events = events

    @property
    def ups(self) -> int:
        """Count of link up events."""
        return sum(1 for e in self._events if e.state == "Up")

    @property
    def downs(self) -> int:
        """Count of link down events."""
        return sum(1 for e in self._events if e.state == "Down")

    @property
    def flap_count(self) -> int:
        """Total number of state changes."""
        return len(self._events)

    def log(self) -> None:
        self._logger.info(
            f"LinkFlapDevice(interface={self._interface!r}, "
            f"ups={self.ups}, downs={self.downs}, "
            f"total_events={self.flap_count})"
        )


class LinkFlapParser(IParser):
    """
    Parser for dmesg output to detect network link flaps.
    Extracts interface up/down events from kernel logs.
    """

    _link_event_pattern: ClassVar[re.Pattern] = re.compile(
        r"(?P<timestamp>\[\s*\d+\.\d+\])?\s*(?P<iface>[a-zA-Z0-9\-_]+):?\s+Link is (?P<state>Up|Down)",
        re.IGNORECASE,
    )

    def __init__(self, raw_output: str):
        IParser.__init__(self, LogName.MAIN.value)

        self._raw_output = raw_output
        self._devices: dict[str, LinkFlapDevice] = {}
        self._parse()

    def name(self) -> str:
        return "link_flap"

    def _parse(self) -> None:
        """Parse dmesg output and extract link events per interface."""
        events_by_iface: dict[str, list[LinkEvent]] = {}

        for line in self._raw_output.splitlines():
            match = self._link_event_pattern.search(line)
            if match:
                iface = match.group("iface")
                state = match.group("state").capitalize()
                timestamp = match.group("timestamp") or "[unknown]"

                event = LinkEvent(timestamp=timestamp, state=state, interface=iface)
                events_by_iface.setdefault(iface, []).append(event)

        # Create LinkFlapDevice objects
        for iface, events in events_by_iface.items():
            self._devices[iface] = LinkFlapDevice(iface, events)

    def get_result(self) -> dict[str, LinkFlapDevice]:
        """Returns dictionary of interface name to LinkFlapDevice."""
        return self._devices

    def get_device(self, interface: str) -> LinkFlapDevice | None:
        """Get link flap data for a specific interface."""
        return self._devices.get(interface)

    def log(self) -> None:
        for device in self._devices.values():
            device.log()
