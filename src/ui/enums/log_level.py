from enum import Enum


class LogLevel(Enum):
    """Logging levels with associated display colors."""

    DEBUG = ("debug", "text-blue-600")
    INFO = ("info", "text-neutral-600")
    WARNING = ("warning", "text-yellow-400")
    ERROR = ("error", "text-red-500")
    CRITICAL = ("critical", "text-red-800")

    @property
    def color(self) -> str:
        """Return the associated color for this log level."""
        return self.value[1]
