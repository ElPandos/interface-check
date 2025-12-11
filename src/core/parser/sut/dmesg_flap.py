from dataclasses import dataclass
from datetime import UTC, datetime as dt
import re
from typing import ClassVar

from src.core.enum.messages import LogMsg
from src.interfaces.component import IParser
from src.platform.enums.log import LogName


@dataclass(frozen=True)
class DmesgEvent:
    """Represents a single link state change event in dmesg."""

    timestamp: dt
    state: str
    interface: str


@dataclass(frozen=True)
class DmesgFlapDevice:
    """Represents a single link flap (down->up cycle)."""

    interface: str
    down_time: dt
    up_time: dt

    @property
    def duration(self) -> float:
        """Flap duration in seconds."""
        return (self.up_time - self.down_time).total_seconds()

    @property
    def csv_row(self) -> str:
        """CSV format: interface,down_time,up_time"""
        return f"{self.interface},{self.down_time.isoformat()},{self.up_time.isoformat()}, {self.duration}"


class DmesgFlapResult:
    """Wrapper for dmesg flap results with property access."""

    def __init__(self, flaps: list[DmesgFlapDevice]):
        self._flaps = flaps

    @property
    def flaps(self) -> list[DmesgFlapDevice]:
        """Get list of all flaps."""
        return self._flaps

    @property
    def down_timestamp(self) -> str:
        """Get most recent flap down timestamp."""
        return self._flaps[-1].down_time.strftime("%Y-%m-%d %H:%M:%S") if self._flaps else ""

    @property
    def up_timestamp(self) -> str:
        """Get most recent flap up timestamp."""
        return self._flaps[-1].up_time.strftime("%Y-%m-%d %H:%M:%S") if self._flaps else ""

    @property
    def duration(self) -> str:
        """Get most recent flap duration."""
        return str(self._flaps[-1].duration) if self._flaps else ""


class SutDmesgFlapParser(IParser):
    """Parser for dmesg output to detect link flaps after start_time."""

    _link_event_pattern: ClassVar[re.Pattern] = re.compile(
        r"(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2},\d+[+-]\d{2}:\d{2})\s+"
        r".*?(?P<iface>\S+):\s+Link\s+(?P<state>up|down)",
        re.IGNORECASE,
    )

    def __init__(self, start_time: dt | None = None):
        """Initialize parser.

        Args:
            start_time: Only parse events after this time (defaults to epoch)
        """
        IParser.__init__(self, LogName.MAIN.value)

        self._start_time = start_time if start_time else dt.fromtimestamp(0, tz=UTC)
        self._result: list[DmesgFlapDevice] = []
        self._raw_data: str | None = None

    @property
    def name(self) -> str:
        return "dmesg_flap"

    def _parse_timestamp(self, ts_str: str) -> dt | None:
        """Parse ISO format timestamp from dmesg -T."""
        try:
            return dt.fromisoformat(ts_str.replace(",", "."))
        except ValueError:
            self._logger.debug(f"{LogMsg.PARSER_TIMESTAMP_FAIL.value}: {ts_str}")
            return None

    def parse(self, raw_data: str) -> None:
        """Parse dmesg output and extract link flaps after start_time."""
        self._log_parse(raw_data)
        self._raw_data = raw_data
        self._result.clear()

        events_by_iface: dict[str, list[DmesgEvent]] = {}

        # Extract all events
        for line in self._raw_data.splitlines():
            match = self._link_event_pattern.search(line)
            if not match:
                continue

            ts = self._parse_timestamp(match.group("timestamp"))
            if not ts or ts <= self._start_time:
                continue

            event = DmesgEvent(
                timestamp=ts, state=match.group("state").lower(), interface=match.group("iface")
            )
            events_by_iface.setdefault(event.interface, []).append(event)

        # Pair down->up events into flaps
        for iface, events in events_by_iface.items():
            events.sort(key=lambda e: e.timestamp)
            i = 0
            while i < len(events) - 1:
                if events[i].state == "down" and events[i + 1].state == "up":
                    device = DmesgFlapDevice(
                        interface=iface,
                        down_time=events[i].timestamp,
                        up_time=events[i + 1].timestamp,
                    )
                    self._result.append(device)
                    i += 2
                else:
                    i += 1

        self._logger.debug(f"[{self.name}] Parsed {len(self._result)} link flaps")

    def get_result(self) -> DmesgFlapResult:
        """Get all detected link flaps and update start_time to latest up_timestamp."""
        if self._result:
            self._start_time = max(f.up_time for f in self._result)
        return DmesgFlapResult(self._result)

    def get_most_recent_status(self) -> tuple[str, str]:
        """Get most recent link status (for backward compatibility)."""
        if self._raw_data is None:
            return "Unknown", ""

        for line in reversed(self._raw_data.splitlines()):
            match = self._link_event_pattern.search(line)
            if match:
                return match.group("state").capitalize(), match.group("timestamp")

        return "Unknown", ""

    def log(self) -> None:
        """Log all flaps in CSV format."""
        self._logger.info("interface,down_time,up_time")
        for flap in self._result:
            self._logger.info(flap.csv_row)
