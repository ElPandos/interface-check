import re
import subprocess
from typing import Dict, Any, Optional
from typing import Any, Dict, List, Union
from pprint import pprint


class EthtoolModuleInfo:
    """
    Represents parsed output from `ethtool -m -v <iface>`.
    Provides structured access to module EEPROM diagnostic information.
    """

    def __init__(self, iface: str, raw_output: str):
        self.iface = iface
        self.raw_output = raw_output
        self.data: Dict[str, Any] = self._parse_output()

    def _normalize_key(self, key: str) -> str:
        """Convert 'Vendor PN' -> 'vendor_pn' for consistent dict keys."""
        return re.sub(r'\s+', '_', key.strip().lower())

    def _parse_output(self) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {}
        for line in self.raw_output.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[self._normalize_key(key)] = value.strip()
        return parsed

    def get(self, field: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieve a parsed field safely.
        Example: module.get("vendor_name")
        """
        return self.data.get(field.lower(), default)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __repr__(self) -> str:
        return f"EthtoolModuleInfo(iface={self.iface!r}, fields={len(self.data)})"

    def from_system(self, iface: str) -> "EthtoolModuleInfo":
        """
        Run `sudo ethtool -m -v <iface>` and parse output.
        """
        result = subprocess.run(
            ["ethtool", "-m", iface],
            text=True,
            capture_output=True,
            check=True
        )
        return self(iface, result.stdout)

class EthtoolParser:
    """
    Parser for 'ethtool -m' style output with support for values containing units.
    Extracts settings into a structured dictionary where values are stored
    as parsed numbers and units when applicable.
    """

    # Regex to capture: number + optional decimal + unit
    _value_with_unit_pattern = re.compile(
        r"([-+]?\d*\.?\d+)\s*([a-zA-Z%°]+(?:\s*[a-zA-Z]+)*)"
    )

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse raw ethtool output into a structured dictionary.

        Args:
            text (str): Raw multiline string from `ethtool -m`.

        Returns:
            Dict[str, Any]: Dictionary with parsed keys and values.
        """
        result: Dict[str, Any] = {}

        for line in text.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if not value:
                result[key] = None
                continue

            # Case 1: Multiple value/unit pairs (separated by "/")
            if "/" in value:
                parts = [p.strip() for p in value.split("/")]
                parsed_parts = [self._parse_value_with_unit(p) for p in parts]
                result[key] = parsed_parts if len(parsed_parts) > 1 else parsed_parts[0]

            # Case 2: Single value with unit
            elif self._value_with_unit_pattern.search(value):
                result[key] = self._parse_value_with_unit(value)

            # Case 3: Hex or string values
            else:
                result[key] = value

        return result

    def _parse_value_with_unit(self, text: str) -> Union[Dict[str, Union[float, str]], str]:
        """
        Parse a single value with unit.

        Args:
            text (str): Value text, e.g. "7.962 mA"

        Returns:
            Dict with numeric value and unit, or raw string if no match.
        """
        match = self._value_with_unit_pattern.search(text)
        if match:
            number, unit = match.groups()
            return {
                "value": float(number),
                "unit": unit.strip()
            }
        return text


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":

    # Replace with your real interface (e.g., "ens2f1np1")
    #iface = "ens2f1np1"
    #module = EthtoolModuleInfo.from_system(iface)

    #print(module)  # Summary
    #print(module.get("vendor_name"))  # Mellanox
    #print(module.get("serial_number"))  # MT1234X56789


    sample = """
    BR, Nominal                               : 25750MBd
    Laser bias current                        : 7.962 mA
    Laser output power                        : 0.8044 mW / -0.95 dBm
    Module temperature                        : 50.14 degrees C / 122.26 degrees F
    Module voltage                            : 3.3036 V
    Vendor name                               : FINISAR CORP.
    """

    sample_2 = """
    Identifier                                : 0x03 (SFP)
    Extended identifier                       : 0x04 (GBIC/SFP defined by 2-wire interface ID)
    Connector                                 : 0x07 (LC)
    Transceiver codes                         : 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x02
    Transceiver type                          : Extended: 100G Base-SR4 or 25GBase-SR
    Encoding                                  : 0x06 (64B/66B)
    BR, Nominal                               : 25750MBd
    Rate identifier                           : 0x00 (unspecified)
    Length (SMF,km)                           : 0km
    Length (SMF)                              : 0m
    Length (50um)                             : 20m
    Length (62.5um)                           : 0m
    Length (Copper)                           : 10m
    Length (OM3)                              : 70m
    Laser wavelength                          : 850nm
    Vendor name                               : FINISAR CORP.
    Vendor OUI                                : 00:90:65
    Vendor PN                                 : FTLF8536P5BCL-HP
    Vendor rev                                : B
    Option values                             : 0x08 0x1a
    Option                                    : RX_LOS implemented
    Option                                    : TX_FAULT implemented
    Option                                    : TX_DISABLE implemented
    Option                                    : Retimer or CDR implemented
    BR margin, max                            : 0%
    BR margin, min                            : 0%
    Vendor SN                                 : MY8327154T
    Date code                                 : 23070827
    Optical diagnostics support               : Yes
    Laser bias current                        : 7.960 mA
    Laser output power                        : 0.8010 mW / -0.96 dBm
    Receiver signal average optical power     : 0.7561 mW / -1.21 dBm
    Module temperature                        : 50.77 degrees C / 123.39 degrees F
    Module voltage                            : 3.3026 V
    Alarm/warning flags implemented           : Yes
    Laser bias current high alarm             : Off
    Laser bias current low alarm              : Off
    Laser bias current high warning           : Off
    Laser bias current low warning            : Off
    Laser output power high alarm             : Off
    Laser output power low alarm              : Off
    Laser output power high warning           : Off
    Laser output power low warning            : Off
    Module temperature high alarm             : Off
    Module temperature low alarm              : Off
    Module temperature high warning           : Off
    Module temperature low warning            : Off
    Module voltage high alarm                 : Off
    Module voltage low alarm                  : Off
    Module voltage high warning               : Off
    Module voltage low warning                : Off
    Laser rx power high alarm                 : Off
    Laser rx power low alarm                  : Off
    Laser rx power high warning               : Off
    Laser rx power low warning                : Off
    Laser bias current high alarm threshold   : 12.000 mA
    Laser bias current low alarm threshold    : 1.000 mA
    Laser bias current high warning threshold : 11.500 mA
    Laser bias current low warning threshold  : 2.000 mA
    Laser output power high alarm threshold   : 2.5119 mW / 4.00 dBm
    Laser output power low alarm threshold    : 0.1259 mW / -9.00 dBm
    Laser output power high warning threshold : 1.9953 mW / 3.00 dBm
    Laser output power low warning threshold  : 0.1585 mW / -8.00 dBm
    Module temperature high alarm threshold   : 75.00 degrees C / 167.00 degrees F
    Module temperature low alarm threshold    : -5.00 degrees C / 23.00 degrees F
    Module temperature high warning threshold : 70.00 degrees C / 158.00 degrees F
    Module temperature low warning threshold  : 0.00 degrees C / 32.00 degrees F
    Module voltage high alarm threshold       : 3.6000 V
    Module voltage low alarm threshold        : 3.0000 V
    Module voltage high warning threshold     : 3.5000 V
    Module voltage low warning threshold      : 3.1000 V
    Laser rx power high alarm threshold       : 2.5119 mW / 4.00 dBm
    Laser rx power low alarm threshold        : 0.0100 mW / -20.00 dBm
    Laser rx power high warning threshold     : 1.9953 mW / 3.00 dBm
    Laser rx power low warning threshold      : 0.0158 mW / -18.01 dBm
    """

    parser = EthtoolParser()
    #parsed = parser.parse(sample)
    parsed = parser.parse(sample_2)

    pprint(parsed)
