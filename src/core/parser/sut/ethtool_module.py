import re

from src.core.parser.sut.common import ParsedDevice, ValueWithUnit
from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class EthtoolModuleDevice(ParsedDevice):
    """Represents parsed ethtool -m module information."""

    def __init__(self, data: dict[str, str]):
        ParsedDevice.__init__(self, LogName.MAIN.value)
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

    @property
    def rx_power(self) -> list[ValueWithUnit] | None:
        power_str = self._data.get("Receiver signal average optical power")
        if power_str:
            return self._parse_power(power_str)
        return None

    @property
    def module_voltage(self) -> ValueWithUnit | None:
        voltage_str = self._data.get("Module voltage")
        if voltage_str:
            return self._parse_single_value(voltage_str)
        return None

    def _parse_temperature(self, temp_str: str) -> list[ValueWithUnit]:
        pattern = r"([\d.]+)\s*degrees\s*([CF])"
        matches = re.findall(pattern, temp_str)
        return [
            ValueWithUnit(float(val), f"degrees {unit}", f"{val} degrees {unit}")
            for val, unit in matches
        ]

    def _parse_power(self, power_str: str) -> list[ValueWithUnit]:
        pattern = r"([\d.-]+)\s*(mW|dBm)"
        matches = re.findall(pattern, power_str)
        return [ValueWithUnit(float(val), unit, f"{val} {unit}") for val, unit in matches]

    def _parse_single_value(self, value_str: str) -> ValueWithUnit | None:
        pattern = r"([\d.-]+)\s*([a-zA-Z%]+)"
        match = re.search(pattern, value_str)
        if match:
            val, unit = match.groups()
            return ValueWithUnit(float(val), unit, f"{val} {unit}")
        return None


class SutEthtoolModuleParser(IParser):
    """Parser for `ethtool -m <interface>` output."""

    def __init__(self):
        IParser.__init__(self, LogName.MAIN.value)
        self._result: dict[str, str] = {}
        self._raw_data: str | None = None

    def name(self) -> str:
        return "ethtool_module"

    def parse(self, raw_data: str) -> None:
        self._log_parse(raw_data)
        self._raw_data = raw_data

        for line in self._raw_data.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                self._result[key.strip()] = value.strip()

        self._logger.debug(f"[{self.name}] Parsed {len(self._result)} key-value pairs")

    def get_result(self) -> EthtoolModuleDevice:
        return EthtoolModuleDevice(self._result)

    def log(self) -> None:
        device = self.get_result()
        self._logger.info(f"Vendor: {device.vendor_name}")
        self._logger.info(f"Part Number: {device.vendor_pn}")
        self._logger.info(f"Serial Number: {device.vendor_sn}")
        if device.module_temperature:
            temps = ", ".join([f"{t.value} {t.unit}" for t in device.module_temperature])
            self._logger.info(f"Temperature: {temps}")
