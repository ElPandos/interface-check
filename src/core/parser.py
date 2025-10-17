import re

import numpy as np


class EyeScanParser:
    """Parse SLX 'phy diag xeX eyescan' CLI output into structured data."""

    _row_pattern = re.compile(r"^\s*([\-]?\d+)mV\s*:\s*([0-9:\-\+\| ]+)$")

    # Map pattern characters to numeric levels (you can tune this mapping)
    _char_map = {
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
        self.raw_output = raw_output
        self.rows: list[dict[str, str]] = self._parse_rows()

    def _parse_rows(self) -> list[dict[str, str]]:
        """Extract voltage/pattern rows from CLI output."""
        rows = []
        for line in self.raw_output.splitlines():
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

    def to_matrix(self) -> tuple[np.ndarray, list[int], list[int]]:
        """
        Convert parsed rows into a numeric 2D matrix for plotting.

        Returns:
            matrix (2D np.ndarray): intensity grid
            voltages (List[int]): Y-axis voltage values
            phase_offsets (List[int]): X-axis phase offset values (-31 to +31)
        """
        voltages = [row["voltage"] for row in self.rows]
        patterns = [row["pattern"] for row in self.rows]
        max_len = max(len(p) for p in patterns)

        # Convert pattern characters → numeric grid
        matrix = np.array([[self._char_map.get(ch, 0) for ch in p.ljust(max_len)] for p in patterns])

        # Create phase offset values from -31 to +31
        phase_offsets = list(range(-31, 32))  # -31 to +31 inclusive

        return matrix, voltages, phase_offsets
