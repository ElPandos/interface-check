from src.interfaces.component import IParser
from src.platform.enums.log import LogName


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
