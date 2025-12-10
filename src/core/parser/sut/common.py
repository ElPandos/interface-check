from dataclasses import dataclass
import logging


class ParsedDevice:
    """Base class for parsed device data."""

    def __init__(self, logger: str):
        self._logger = logging.getLogger(logger)


@dataclass(frozen=True)
class ValueWithUnit:
    """Represents a value with its unit."""

    value: float
    unit: str
    raw: str

    def __str__(self) -> str:
        return f"{self.value:.6f}"
