from dataclasses import dataclass
from datetime import UTC, datetime as dt
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
    """Base class for parsed device data.

    Args:
        logger: Logger name for this device
    """

    def __init__(self, logger: str):
        self._logger = logging.getLogger(logger)


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
        self._rows: list[dict[str, str]] = []

        self._parse()

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "eye_scan"

    def _parse(self) -> list[dict[str, str]]:
        """Extract voltage/pattern rows from CLI output.

        Returns:
            List of voltage/pattern dictionaries
        """
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
        """Convert parsed rows into numeric 2D matrix for plotting.

        Returns:
            Tuple of (matrix, voltages, phase_offsets)
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
        pass


# ---------------------------------------------------------------------------- #
#                                      MST                                     #
# ---------------------------------------------------------------------------- #


class MstVersionDevice(ParsedDevice):
    """Mellanox/NVIDIA device entry from mst status -v."""

    def __init__(
        self,
        device_type: str,
        mst: str,
        pci: str,
        rdma: str | None,
        net: str | None,
        numa: str | None,
    ):
        """Initialize MST device.

        Args:
            device_type: Device type identifier
            mst: MST device path
            pci: PCI address
            rdma: RDMA device name
            net: Network interface name
            numa: NUMA node
        """
        ParsedDevice.__init__(self, LogName.CORE_MAIN.value)

        self.device_type = device_type
        self.mst = mst
        self.pci = pci
        self.rdma = rdma if rdma != "-" else None
        self.net = net.replace("net-", "") if net and net.startswith("net-") else net
        self.numa = numa if numa != "-" else None

    def log(self) -> str:
        """Log device information.

        Returns:
            Formatted device info string
        """
        self._logger.info(
            f"MstDevice(device_type={self.device_type!r}, "
            f"mst={self.mst!r}, pci={self.pci!r}, "
            f"rdma={self.rdma!r}, net={self.net!r}, "
            f"numa={self.numa!r})"
        )


class MstStatusVersionParser(IParser):
    """Parser for mst status -v output."""

    def __init__(self, raw_output: str):
        """Initialize parser.

        Args:
            raw_output: Raw command output
        """
        IParser.__init__(self, LogName.CORE_MAIN.value)

        self._raw_output = raw_output
        self._devices: list[MstVersionDevice] = []

        self._parse()

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "mst_version"

    def _parse(self) -> None:
        """Parse MST status output."""
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
        """Get parsed devices.

        Returns:
            List of MST devices
        """
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
        """Log all devices."""
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

    def __str__(self) -> str:
        """Format value with 3 decimal places.

        Returns:
            Formatted string
        """
        return f"{self.value:.3f}"


class EthtoolModuleDevice(ParsedDevice):
    """Represents parsed ethtool -m module information."""

    def __init__(self, data: dict[str, str]):
        """Initialize module device.

        Args:
            data: Parsed key-value data
        """
        ParsedDevice.__init__(self, LogName.CORE_MAIN.value)

        self._data = data

    @property
    def module_temperature(self) -> list[ValueWithUnit] | None:
        """Get module temperature.

        Returns:
            Temperature values or None
        """
        temp_str = self._data.get("Module temperature")
        if temp_str:
            return self._parse_temperature(temp_str)
        return None

    @property
    def laser_bias_current(self) -> ValueWithUnit | None:
        """Get laser bias current.

        Returns:
            Current value or None
        """
        current_str = self._data.get("Laser bias current")
        if current_str:
            return self._parse_single_value(current_str)
        return None

    @property
    def laser_output_power(self) -> list[ValueWithUnit] | None:
        """Get laser output power.

        Returns:
            Power values or None
        """
        power_str = self._data.get("Laser output power")
        if power_str:
            return self._parse_power(power_str)
        return None

    def _parse_temperature(self, temp_str: str) -> list[ValueWithUnit]:
        """Parse temperature string.

        Args:
            temp_str: Temperature string

        Returns:
            List of temperature values
        """
        pattern = r"([\d.]+)\s*degrees\s*([CF])"
        matches = re.findall(pattern, temp_str)
        return [
            ValueWithUnit(float(val), f"degrees {unit}", f"{val} degrees {unit}")
            for val, unit in matches
        ]

    def _parse_power(self, power_str: str) -> list[ValueWithUnit]:
        """Parse power string.

        Args:
            power_str: Power string

        Returns:
            List of power values
        """
        pattern = r"([\d.-]+)\s*(mW|dBm)"
        matches = re.findall(pattern, power_str)
        return [ValueWithUnit(float(val), unit, f"{val} {unit}") for val, unit in matches]

    def _parse_single_value(self, value_str: str) -> ValueWithUnit | None:
        """Parse single value with unit.

        Args:
            value_str: Value string

        Returns:
            Parsed value or None
        """
        pattern = r"([\d.-]+)\s*([a-zA-Z%]+)"
        match = re.search(pattern, value_str)
        if match:
            val, unit = match.groups()
            return ValueWithUnit(float(val), unit, f"{val} {unit}")
        return None


class EthtoolModuleParser(IParser):
    """Parser for `ethtool -m <interface>` output."""

    def __init__(self, raw_output: str):
        """Initialize parser.

        Args:
            raw_output: Raw command output
        """
        IParser.__init__(self, LogName.CORE_MAIN.value)

        self._raw_output = raw_output
        self._result: dict[str, str] = {}

        self._parse()

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "ethtool_module"

    def _parse(self) -> None:
        """Parse key-value pairs from ethtool -m output."""
        for line in self._raw_output.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                self._result[key.strip()] = value.strip()

    def get_result(self) -> EthtoolModuleDevice:
        """Return parsed module device.

        Returns:
            Parsed module device
        """
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
        """Initialize mlxlink device.

        Args:
            data: Parsed key-value data
        """
        ParsedDevice.__init__(self, LogName.CORE_MAIN.value)

        self._data = data

    @property
    def state(self) -> str | None:
        """Get link state.

        Returns:
            Link state or None
        """
        return self._data.get("State")

    @property
    def speed(self) -> str | None:
        """Get link speed.

        Returns:
            Link speed or None
        """
        return self._data.get("Speed")

    @property
    def temperature(self) -> ValueWithUnit | None:
        """Get temperature.

        Returns:
            Temperature value or None
        """
        temp_str = self._data.get("Temperature [C]")
        if temp_str:
            return self._parse_temperature_with_range(temp_str)
        return None

    @property
    def voltage(self) -> ValueWithUnit | None:
        """Get voltage.

        Returns:
            Voltage value or None
        """
        voltage_str = self._data.get("Voltage [mV]")
        if voltage_str:
            return self._parse_value_with_range(voltage_str)
        return None

    @property
    def bias_current(self) -> ValueWithUnit | None:
        """Get bias current.

        Returns:
            Current value or None
        """
        current_str = self._data.get("Bias Current [mA]")
        if current_str:
            return self._parse_value_with_range(current_str)
        return None

    @property
    def rx_power(self) -> ValueWithUnit | None:
        """Get RX power.

        Returns:
            RX power value or None
        """
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
        """Get TX power.

        Returns:
            TX power value or None
        """
        power_str = self._data.get("Tx Power Current [dBm]")
        if power_str:
            return self._parse_value_with_range(power_str)
        return None

    @property
    def vendor_name(self) -> str | None:
        """Get vendor name.

        Returns:
            Vendor name or None
        """
        return self._data.get("Vendor Name")

    @property
    def vendor_part_number(self) -> str | None:
        """Get vendor part number.

        Returns:
            Part number or None
        """
        return self._data.get("Vendor Part Number")

    @property
    def vendor_serial_number(self) -> str | None:
        """Get vendor serial number.

        Returns:
            Serial number or None
        """
        return self._data.get("Vendor Serial Number")

    @property
    def time_since_last_clear(self) -> ValueWithUnit | None:
        """Get time since last clear.

        Returns:
            Time value or None
        """
        time_str = self._data.get("Time Since Last Clear [Min]")
        if time_str and time_str != "N/A":
            return self._parse_scientific_value(time_str, "Min")
        return None

    @property
    def effective_physical_errors(self) -> ValueWithUnit | None:
        """Get effective physical errors.

        Returns:
            Error count or None
        """
        errors_str = self._data.get("Effective Physical Errors")
        if errors_str and errors_str != "N/A":
            return self._parse_scientific_value(errors_str, "")
        return None

    @property
    def effective_physical_ber(self) -> ValueWithUnit | None:
        """Get effective physical BER.

        Returns:
            BER value or None
        """
        ber_str = self._data.get("Effective Physical BER")
        if ber_str and ber_str != "N/A":
            return self._parse_scientific_value(ber_str, "")
        return None

    @property
    def raw_physical_errors_per_lane(self) -> ValueWithUnit | None:
        """Get raw physical errors per lane.

        Returns:
            Error count or None
        """
        errors_str = self._data.get("Raw Physical Errors Per Lane")
        if errors_str and errors_str != "N/A":
            return self._parse_scientific_value(errors_str, "")
        return None

    @property
    def raw_physical_ber(self) -> ValueWithUnit | None:
        """Get raw physical BER.

        Returns:
            BER value or None
        """
        ber_str = self._data.get("Raw Physical BER")
        if ber_str and ber_str != "N/A":
            return self._parse_scientific_value(ber_str, "")
        return None

    def _parse_temperature_with_range(self, temp_str: str) -> ValueWithUnit | None:
        """Parse temperature with range.

        Args:
            temp_str: Temperature string

        Returns:
            Parsed value or None
        """
        pattern = r"([\d.-]+)"
        match = re.search(pattern, temp_str)
        if match:
            return ValueWithUnit(float(match.group(1)), "C", temp_str)
        return None

    def _parse_value_with_range(self, value_str: str) -> ValueWithUnit | None:
        """Parse value with range.

        Args:
            value_str: Value string

        Returns:
            Parsed value or None
        """
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
        """Parse scientific notation values.

        Args:
            value_str: Value string
            unit: Unit string

        Returns:
            Parsed value or None
        """
        pattern = r"([\d.-]+[Ee][+-]?\d+|[\d.-]+)"
        match = re.search(pattern, value_str)
        if match:
            try:
                return ValueWithUnit(float(match.group(1)), unit, value_str)
            except ValueError:
                return None
        return None


class MlxlinkParser(IParser):
    """Parser for mlxlink command output."""

    def __init__(self, raw_output: str):
        """Initialize parser.

        Args:
            raw_output: Raw command output
        """
        IParser.__init__(self, LogName.CORE_MAIN.value)

        self._raw_output = raw_output
        self._result: dict[str, str] = {}

        self._parse()

    @property
    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "mlxlink"

    def _parse(self) -> None:
        """Parse key-value pairs from mlxlink output."""
        if self._raw_output is not None:
            for line in self._raw_output.splitlines():
                if ":" in line and not line.strip().endswith(":"):
                    key, value = line.split(":", 1)
                    self._result[key.strip()] = value.strip()

    def get_result(self) -> MlxlinkDevice:
        """Return parsed mlxlink device.

        Returns:
            Parsed device
        """
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
#                           Dmesg - Link flap parser                           #
# ---------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DmesgEvent:
    """Represents a single link state change event in dmesg."""

    timestamp: str  # Local time formatted as YYYY-MM-DD HH:MM:SS
    state: str  # "Up" or "Down"
    interface: str
    raw_timestamp: str  # Original timestamp from dmesg


class DmesgFlapDevice(ParsedDevice):
    """Represents link flap statistics for a single network interface in dmesg."""

    def __init__(self, interface: str, events: list[DmesgEvent]):
        """Initialize flap device.

        Args:
            interface: Network interface name
            events: List of link events
        """
        ParsedDevice.__init__(self, LogName.CORE_MAIN.value)

        self._interface = interface
        self._events = events

    @property
    def ups(self) -> int:
        """Count of link up events.

        Returns:
            Number of up events
        """
        return sum(1 for e in self._events if e.state == "Up")

    @property
    def downs(self) -> int:
        """Count of link down events.

        Returns:
            Number of down events
        """
        return sum(1 for e in self._events if e.state == "Down")

    @property
    def flap_count(self) -> int:
        """Total number of state changes.

        Returns:
            Total event count
        """
        return len(self._events)

    def log(self) -> None:
        """Log flap statistics."""
        self._logger.info(
            f"LinkFlapDevice(interface={self._interface!r}, "
            f"ups={self.ups}, downs={self.downs}, "
            f"total_events={self.flap_count})"
        )


class DmesgFlapParser(IParser):
    """Parser for dmesg -T output to detect network link flaps."""

    _link_event_pattern: ClassVar[re.Pattern] = re.compile(
        r"\[(?P<timestamp>[^\]]+)\]\s+.*?(?P<iface>[a-zA-Z0-9\-_]+):\s+Link\s+(?:is\s+)?(?P<state>up|down)",
        re.IGNORECASE,
    )

    def __init__(self, raw_output: str = ""):
        """Initialize parser.

        Args:
            raw_output: Raw dmesg output
        """
        IParser.__init__(self, LogName.CORE_MAIN.value)

        self._raw_output = raw_output
        self._devices: dict[str, DmesgFlapDevice] = {}

        if raw_output:
            self._parse()

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "link_flap"

    def _parse_timestamp(self, ts_str: str) -> str:
        """Parse dmesg -T timestamp and convert to local time.

        Args:
            ts_str: Timestamp string from dmesg -T (e.g., 'Sun Nov  9 05:15:04 2025')

        Returns:
            Formatted local timestamp as 'YYYY-MM-DD HH:MM:SS'
        """
        try:
            dt_utc = dt.strptime(ts_str, "%a %b %d %H:%M:%S %Y")
            dt_local = dt_utc.replace(tzinfo=UTC).astimezone()
            return dt_local.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            self._logger.debug(f"Failed to parse timestamp: '{ts_str}': {e}")
            return ts_str

    def _parse(self) -> None:
        """Parse dmesg output and extract link events per interface."""
        events_by_iface: dict[str, list[DmesgEvent]] = {}

        for line in self._raw_output.splitlines():
            match = self._link_event_pattern.search(line)
            if match:
                iface = match.group("iface")
                state = match.group("state").capitalize()
                raw_ts = match.group("timestamp") or "unknown"

                # Convert timestamp to local time
                local_ts = self._parse_timestamp(raw_ts) if raw_ts != "unknown" else ""

                event = DmesgEvent(
                    timestamp=local_ts, state=state, interface=iface, raw_timestamp=raw_ts
                )
                events_by_iface.setdefault(iface, []).append(event)

        # Create LinkFlapDevice objects
        for iface, events in events_by_iface.items():
            self._devices[iface] = DmesgFlapDevice(iface, events)

    def get_most_recent_status(self) -> tuple[str, str]:
        """Get the most recent link status from all interfaces.

        Returns:
            Tuple of (status, timestamp) where status is 'Up', 'Down', or 'Unknown'
        """
        if not self._raw_output:
            self._logger.debug("No dmesg output to parse")
            return "Unknown", ""

        lines = self._raw_output.strip().split("\n")
        self._logger.debug(f"Parsing {len(lines)} dmesg lines for most recent link status")

        # Search from bottom up for most recent state
        for line in reversed(lines):
            match = self._link_event_pattern.search(line)
            if match:
                state = match.group("state").capitalize()
                raw_ts = match.group("timestamp") or ""
                local_ts = self._parse_timestamp(raw_ts) if raw_ts else ""

                self._logger.debug(f"Found most recent link state: {state} at {local_ts}")
                return state, local_ts

        self._logger.debug("No link status found in dmesg output")
        return "Unknown", ""

    def get_result(self) -> dict[str, DmesgFlapDevice]:
        """Returns dictionary of interface name to LinkFlapDevice.

        Returns:
            Dictionary mapping interface to flap device
        """
        return self._devices

    def get_device(self, interface: str) -> DmesgFlapDevice | None:
        """Get link flap data for a specific interface.

        Args:
            interface: Network interface name

        Returns:
            Flap device or None
        """
        return self._devices.get(interface)

    def log(self) -> None:
        """Log all devices."""
        for device in self._devices.values():
            device.log()
