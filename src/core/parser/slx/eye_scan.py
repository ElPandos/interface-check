import re
from typing import ClassVar

import numpy as np

from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class SlxEyeParser(IParser):
    """Parse SLX 'phy diag xeX eyescan' CLI output into structured data."""

    _row_pattern = re.compile(r"^\s*([\-]?\d+)mV\s*:\s*([0-9:\-\+\| ]+)$")

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
        matrix = np.array([[self._char_map.get(ch, 0) for ch in p.ljust(max_len)] for p in patterns])

        # Create phase offset values from -31 to +31
        phase_offsets = list(range(-31, 32))

        return matrix, voltages, phase_offsets

    def log(self) -> None:
        """Log parsed eye scan data."""
