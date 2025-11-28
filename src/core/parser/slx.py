import re
from typing import ClassVar

import numpy as np

from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class SlxEyeParser(IParser):
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

    def __init__(self):
        IParser.__init__(self, LogName.SLX_EYE_SCANNER.value)

        self._rows: list[dict[str, str]] = []
        self._raw_data: str | None = None

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "eye_scan"

    def parse(self, raw_data: str) -> list[dict[str, str]]:
        """Extract voltage/pattern rows from CLI output.

        Returns:
            List of voltage/pattern dictionaries
        """
        self._log_parse(raw_data)
        self._raw_data = raw_data

        rows = []
        for line in self._raw_data.splitlines():
            match = self._row_pattern.match(line)
            if match:
                voltage, pattern = match.groups()
                rows.append(
                    {
                        "voltage": int(voltage.strip()),
                        "pattern": pattern.rstrip(),
                    }
                )
        self._logger.debug(f"[{self.name()}] Parsed {len(rows)} voltage rows")
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


class SlxDscParser(IParser):
    """Parser for SLX 'phy diag xeX dsc' diagnostic output.

    Extracts CORE and lane (LN) diagnostic data from SLX switch.
    """

    def __init__(self):
        """Initialize parser."""
        IParser.__init__(self, LogName.MAIN.value)
        self._core_data: str = ""
        self._lane_data: list[str] = []
        self._raw_data: str | None = None
        self._first_parse = True

    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "slx_dsc"

    def parse(self, raw_data: str) -> None:
        """Parse SLX DSC output and extract CORE and LN data rows.

        Args:
            raw_data: Raw command output
        """
        self._log_parse(raw_data)
        self._raw_data = raw_data
        self._core_data = ""
        self._lane_data = []

        lines = self._raw_data.strip().split("\n")

        # Find CORE header and data
        for i, line in enumerate(lines):
            if line.startswith("CORE RST_ST"):
                if i + 1 < len(lines):
                    if self._first_parse:
                        self._core_data = line + "\n" + lines[i + 1]
                    else:
                        self._core_data = lines[i + 1]
                break

        # Find LN header and data rows
        for i, line in enumerate(lines):
            if line.startswith("LN (CDRxN"):
                if self._first_parse:
                    self._lane_data.append(line)
                # Collect all lane data rows (start with space + digit)
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() and lines[j][0].isspace() and lines[j].strip()[0].isdigit():
                        self._lane_data.append(lines[j])
                    elif lines[j].strip() and not lines[j].startswith("*"):
                        break
                break

        self._first_parse = False
        self._logger.debug(f"[{self.name()}] Parsed {len(self._lane_data)} lane rows")

    def get_result(self) -> str:
        """Get parsed data rows.

        Returns:
            Combined CORE and LN data as newline-separated string
        """
        result = []
        if self._core_data:
            result.append(self._core_data)
        if self._lane_data:
            result.extend(self._lane_data)
        return "\n".join(result)

    def log(self) -> None:
        """Log parsed data."""
        self._logger.debug(f"Core data length: {len(self._core_data)}")
        self._logger.debug(f"Lane data rows: {len(self._lane_data)}")
