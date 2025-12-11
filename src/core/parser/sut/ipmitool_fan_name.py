"""Parser for ipmitool fan sensor names."""

import re


class SutIpmitoolFanNameParser:
    """Parse fan sensor names from ipmitool output."""

    def parse(self, output: str) -> dict[str, str]:
        """Extract fan sensor names.

        Args:
            output: ipmitool sensor output

        Returns:
            Dictionary with fan names as keys and empty strings as values
        """
        pattern = r"^(Fan \d+ (?:Front|Rear) Tach)\s+\|"
        return {match.group(1): "" for match in re.finditer(pattern, output, re.MULTILINE)}
