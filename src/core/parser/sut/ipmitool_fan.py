"""Parser for ipmitool fan sensor output."""

import re


class SutIpmitoolFanParser:
    """Parser for ipmitool sensor fan data."""

    def __init__(self):
        """Initialize parser."""
        self._result = {}

    def parse(self, output: str) -> dict[str, str]:
        """Parse ipmitool sensor output for fan RPMs.

        Args:
            output: Raw ipmitool sensor output

        Returns:
            Dictionary with fan names as keys and RPM values as strings
        """
        self._result = {}

        # Pattern: Fan X Front/Rear Tach | 8528.000   | RPM        | ok
        pattern = r"(Fan\s+\d+\s+(?:Front|Rear)\s+Tach)\s+\|\s+([\d\.]+)\s+\|\s+RPM"

        for line in output.splitlines():
            match = re.search(pattern, line)
            if match:
                fan_name = match.group(1).strip()
                rpm_value = match.group(2).strip()
                self._result[fan_name] = rpm_value

        return self._result

    def parse_attributes(self, output: str) -> list[str]:
        """Parse ipmitool sensor output to extract fan attribute names.

        Args:
            output: Raw ipmitool sensor output

        Returns:
            List of fan names
        """
        attributes = []
        pattern = r"(Fan\s+\d+\s+(?:Front|Rear)\s+Tach)\s+\|"

        for line in output.splitlines():
            match = re.search(pattern, line)
            if match:
                attributes.append(match.group(1).strip())

        return attributes

    def get_result(self) -> dict[str, str]:
        """Get parsed result.

        Returns:
            Dictionary with fan names and RPM values
        """
        return self._result
