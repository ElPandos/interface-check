import re

from src.core.parser.sut.common import ParsedDevice, ValueWithUnit
from src.interfaces.component import IParser
from src.platform.enums.log import LogName


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

    @property
    def physical_grade(self) -> str | None:
        return self._data.get("Physical Grade")

    @property
    def height_eye(self) -> ValueWithUnit | None:
        height_str = self._data.get("Height Eye Opening [mV]")
        if height_str and height_str != "N/A":
            return self._parse_value_with_range(height_str)
        return None

    @property
    def phase_eye(self) -> ValueWithUnit | None:
        phase_str = self._data.get("Phase  Eye Opening [psec]")
        if phase_str and phase_str != "N/A":
            return self._parse_value_with_range(phase_str)
        return None

    def _parse_temperature_with_range(self, temp_str: str) -> ValueWithUnit | None:
        pattern = r"([\d.-]+)"
        match = re.search(pattern, temp_str)
        if match:
            return ValueWithUnit(float(match.group(1)), "C", temp_str)
        return None

    def _parse_value_with_range(self, value_str: str) -> ValueWithUnit | None:
        pattern = r"([\d.-]+)"
        match = re.search(pattern, value_str)
        if match:
            unit_match = re.search(r"\[([a-zA-Z]+)\]", value_str)
            unit = unit_match.group(1) if unit_match else ""
            parsed_value = float(match.group(1))
            if parsed_value == -40.0:
                self._logger.debug(f"Parsed -40.0 from value_str: '{value_str}', matched: '{match.group(1)}'")
            return ValueWithUnit(parsed_value, unit, value_str)
        return None

    def _parse_scientific_value(self, value_str: str, unit: str) -> ValueWithUnit | None:
        pattern = r"([\d.-]+[Ee][+-]?\d+|[\d.-]+)"
        match = re.search(pattern, value_str)
        if match:
            try:
                return ValueWithUnit(float(match.group(1)), unit, value_str)
            except ValueError:
                return None
        return None


class SutMlxlinkParser(IParser):
    """Parser for mlxlink command output from SUT system."""

    def __init__(self):
        IParser.__init__(self, LogName.MAIN.value)
        self._result: dict[str, str] = {}
        self._raw_data: str | None = None

    @property
    def name(self) -> str:
        return "mlxlink"

    def parse(self, raw_data: str) -> None:
        self._log_parse(raw_data)
        self._raw_data = raw_data

        for line in self._raw_data.splitlines():
            if ":" in line and not line.strip().endswith(":"):
                key, value = line.split(":", 1)
                self._result[key.strip()] = value.strip()

        self._logger.debug(f"[{self.name}] Parsed {len(self._result)} key-value pairs")

    def get_result(self) -> MlxlinkDevice:
        return MlxlinkDevice(self._result)

    def log(self) -> None:
        device = self.get_result()
        self._logger.info(f"State: {device.state}")
        self._logger.info(f"Speed: {device.speed}")
        self._logger.info(f"Vendor: {device.vendor_name}")
        if device.temperature:
            self._logger.info(f"Temperature: {device.temperature.value} {device.temperature.unit}")
        if device.voltage:
            self._logger.info(f"Voltage: {device.voltage.value} {device.voltage.unit}")
