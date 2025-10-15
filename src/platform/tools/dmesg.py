"""Dmesg CLI tool implementation."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.mixins.tool import Tool


@dataclass(frozen=True)
class DmesgEntry:
    """Dmesg log entry."""

    timestamp: datetime | None
    facility: str
    level: str
    message: str


class DmesgTool(Tool):
    """Dmesg kernel message diagnostic tool."""

    @property
    def tool_name(self) -> str:
        return "dmesg"

    def get_commands(self) -> dict[str, str]:
        """Get available dmesg commands."""
        return {
            "recent": "dmesg -T | tail -100",
            "network": "dmesg -T | grep -i 'eth\\|net\\|link'",
            "errors": "dmesg -T | grep -i 'error\\|fail\\|warn'",
            "all": "dmesg -T",
        }

    def parse_output(self, _command_name: str, raw_output: str) -> Any:
        """Parse dmesg command output."""
        return self._parse_dmesg_entries(raw_output)

    def _parse_dmesg_entries(self, output: str) -> list[DmesgEntry]:
        """Parse dmesg entries with timestamps."""
        entries = []
        lines = output.strip().split("\n")

        for line in lines:
            if not line.strip():
                continue

            # Parse timestamp if present
            timestamp = None
            if line.startswith("["):
                try:
                    # Extract timestamp from [timestamp] format
                    end_bracket = line.find("]")
                    if end_bracket > 0:
                        timestamp_str = line[1:end_bracket]
                        # Handle both human readable and epoch formats
                        if timestamp_str.count(" ") >= 2:  # Human readable
                            timestamp = datetime.strptime(timestamp_str[:19], "%Y-%m-%d %H:%M:%S").replace(
                                tzinfo=datetime.UTC
                            )
                        message = line[end_bracket + 1 :].strip()
                    else:
                        message = line
                except (ValueError, IndexError):
                    message = line
            else:
                message = line

            entries.append(
                DmesgEntry(
                    timestamp=timestamp,
                    facility="kernel",
                    level="info",  # Default level
                    message=message,
                )
            )

        return entries
