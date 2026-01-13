import re
from typing import ClassVar

from src.interfaces.component import IParser
from src.platform.enums.log import LogName


class SutTimeParser(IParser):
    """Parser for 'time' command output to extract real execution time from SUT.

    Supports multiple time command formats:
    - bash: real 0m0.002s
    - zsh: 0,01s user 0,01s system 75% cpu 0,027 total
    - GNU time: 0:00.10elapsed
    """

    _bash_pattern: ClassVar[re.Pattern] = re.compile(r"^real\s+(\d+)m([\d.,]+)s$", re.MULTILINE)
    _zsh_pattern: ClassVar[re.Pattern] = re.compile(r"cpu\s+([\d.,]+)\s+total$", re.MULTILINE)
    _gnu_pattern: ClassVar[re.Pattern] = re.compile(r"(\d+):(\d+)\.([\d]+)elapsed", re.MULTILINE)

    def __init__(self, logger_name: str = LogName.MAIN.value):
        """Initialize parser.

        Args:
            logger_name: Logger name for this parser
        """
        IParser.__init__(self, logger_name)

        self._real_time_ms: float = 0.0
        self._raw_data: str | None = None

    @property
    def name(self) -> str:
        """Get parser name.

        Returns:
            Parser identifier
        """
        return "time_command"

    def parse(self, raw_data: str) -> None:
        """Parse time command output and extract real time.

        Handles both bash and zsh time output formats.

        Args:
            raw_data: Raw command output including time statistics
        """
        self._log_parse(raw_data)
        self._raw_data = raw_data
        self._real_time_ms = 0.0

        # Try bash format first
        match = self._bash_pattern.search(raw_data)
        if match:
            minutes = int(match.group(1))
            seconds = float(match.group(2).replace(",", "."))
            self._real_time_ms = (minutes * 60 + seconds) * 1000
            self._logger.debug(f"[{self.name}] Bash format: {minutes} m {seconds}s -> {self._real_time_ms:.3f}ms")
            return

        # Try zsh format
        match = self._zsh_pattern.search(raw_data)
        if match:
            seconds = float(match.group(1).replace(",", "."))
            self._real_time_ms = seconds * 1000
            self._logger.debug(f"[{self.name}] Zsh format: {seconds}s -> {self._real_time_ms:.3f}ms")
            return

        # Try GNU time format (0:00.10elapsed)
        match = self._gnu_pattern.search(raw_data)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            subseconds = float(f"0.{match.group(3)}")
            total_seconds = minutes * 60 + seconds + subseconds
            self._real_time_ms = total_seconds * 1000
            self._logger.debug(
                f"[{self.name}] GNU format: {minutes}:{seconds}.{match.group(3)} -> {self._real_time_ms:.3f}ms"
            )
            return

        self._logger.debug(f"[{self.name}] No match found")

    def get_result(self) -> float:
        """Get parsed real time in milliseconds.

        Returns:
            Real execution time in milliseconds
        """
        return self._real_time_ms

    def log(self) -> None:
        """Log parsed time."""
        self._logger.debug(f"Real time: {self._real_time_ms:.3f}ms")
