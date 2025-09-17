from enum import Enum


class LogLevel(Enum):
    """Logging levels with associated display colors."""

    DEBUG = ("debug", "text-blue-600")
    INFO = ("info", "text-neutral-600")
    WARNING = ("warning", "text-yellow-400")
    ERROR = ("error", "text-red-500")
    CRITICAL = ("critical", "text-red-800")

    def __init__(self, value: str, color: str) -> None:
        self._value = value
        self._color = color

    @property
    def name(self) -> str:
        """Return the enum value name."""
        return self._value

    @property
    def color(self) -> str:
        """Return the associated color for this log level."""
        return self._color
