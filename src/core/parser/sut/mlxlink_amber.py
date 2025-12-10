from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class SutMlxlinkAmberParser(IParser):
    """Parser for mlxlink --amber_collect CSV output from SUT system.

    Extracts CSV data rows, including header on first parse.
    """

    def __init__(self):
        """Initialize parser."""
        IParser.__init__(self, LogName.MAIN.value)
        self._data_row: str = ""
        self._raw_data: str | None = None
        self._first_parse = True

    @property
    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "mlxlink_amber"

    def parse(self, raw_data: str) -> None:
        """Parse amber output and extract data row (include header on first parse or when only one data line).

        Args:
            raw_data: Raw command output
        """
        self._log_parse(raw_data)
        self._raw_data = raw_data
        self._data_row = ""

        lines = self._raw_data.strip().split("\n")
        csv_lines = [l for l in lines if l and (l.startswith("amBer_Version") or l[0].isdigit())]

        if self._first_parse and len(csv_lines) >= 2:
            self._data_row = "begin_timestamp," + csv_lines[0] + "\n" + csv_lines[1]
            self._first_parse = False
        elif len(csv_lines) > 1:
            self._data_row = csv_lines[-1]

        self._logger.debug(f"[{self.name}] Parsed data row")

    def get_result(self) -> str:
        """Get parsed data row.

        Returns:
            CSV data row (with header on first parse, data only on subsequent parses)
        """
        return self._data_row

    def log(self) -> None:
        """Log parsed data."""
        self._logger.debug(f"Data row length: {len(self._data_row)}")
