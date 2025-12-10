from dataclasses import dataclass

from src.interfaces.component import IParser
from src.platform.enums.log import LogName


@dataclass(frozen=True)
class TxErrorsResult:
    """TX errors result."""

    tx_errors: int


class SutTxErrorsParser(IParser):
    """Parser for /sys/class/net/*/statistics/tx_errors output."""

    def __init__(self):
        """Initialize parser with baseline value."""
        IParser.__init__(self, LogName.MAIN.value)
        self._baseline: int | None = None
        self._current: int | None = None

    @property
    def name(self) -> str:
        return "tx_errors"

    def parse(self, output: str) -> None:
        """Parse tx_errors value.

        Args:
            output: Command output (single integer value)
        """
        self._log_parse(output)
        try:
            value = int(output.strip())
            if self._baseline is None:
                self._baseline = value
            self._current = value
        except (ValueError, AttributeError):
            self._current = None

    def get_result(self) -> TxErrorsResult | None:
        """Get parsed result only if value changed from baseline.

        Returns:
            TxErrorsResult if value changed, None otherwise
        """
        if self._current is None or self._baseline is None:
            return None
        if self._current == self._baseline:
            return None
        return TxErrorsResult(tx_errors=self._current)

    def log(self) -> None:
        """Log current tx_errors value."""
        if self._current is not None:
            self._logger.info(f"TX Errors: {self._current}")
