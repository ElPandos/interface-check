from dataclasses import dataclass
import re
from typing import Any

DATA = """Identifier                                : 0x03 (SFP)
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
        Vendor SN                                 : MY832713QW
        Date code                                 : 23070727
        Optical diagnostics support               : Yes
        Laser bias current                        : 7.956 mA
        Laser output power                        : 0.7572 mW / -1.21 dBm
        Receiver signal average optical power     : 0.7457 mW / -1.27 dBm
        Module temperature                        : 53.13 degrees C / 127.63 degrees F
        Module voltage                            : 3.3011 V
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


@dataclass
class ValueWithUnit:
    """Holds a numeric value and its corresponding unit."""

    value: float
    unit: str
    raw: str = ""


class EthtoolOutputParser:
    """
    Parses raw 'ethtool -m' SFP module output into structured data.
    Each measurable value is stored as a ValueWithUnit object.
    """

    # Regular expression to match a number + unit pattern
    VALUE_UNIT_RE = re.compile(r"([-+]?\d*\.?\d+)\s*([a-zA-Z%°]+)")

    def parse(self, raw_text: str) -> dict[str, Any]:
        """
        Parse the given raw ethtool output into a dictionary of structured data.
        """
        data: dict[str, Any] = {}

        for line in raw_text.splitlines():
            if ":" not in line:
                continue  # skip lines without key-value pairs

            key, value = [part.strip() for part in line.split(":", 1)]

            # Try to extract all numeric+unit pairs from the value
            matches = list(self.VALUE_UNIT_RE.finditer(value))

            if matches:
                # If multiple (e.g., "0.7572 mW / -1.21 dBm"), store as list
                parsed_values = [
                    ValueWithUnit(value=float(m.group(1)), unit=m.group(2), raw=m.group(0)) for m in matches
                ]
                data[key] = parsed_values if len(parsed_values) > 1 else parsed_values[0]
            else:
                # Non-numeric values (like "FINISAR CORP.")
                data[key] = value or None

        return data


if __name__ == "__main__":
    parser = EthtoolOutputParser()
    parsed = parser.parse(DATA)

    # Example: access structured values
    print(parsed["Module temperature"])
    # → ValueWithUnit(value=53.13, unit='degrees', raw='53.13 degrees C')

    print(parsed["Laser output power"])
    # → [ValueWithUnit(value=0.7572, unit='mW'), ValueWithUnit(value=-1.21, unit='dBm')]
