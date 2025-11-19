"""Worker statistics tracking and reporting."""

from collections import deque
from dataclasses import dataclass, field


@dataclass
class WorkerStats:
    """Statistics for a single worker.

    Tracks command execution durations with rolling mean of last 20 executions.
    """

    command: str
    durations: deque[float] = field(default_factory=lambda: deque(maxlen=20))

    def add_duration(self, duration_ms: float) -> None:
        """Add command duration to rolling window.

        Args:
            duration_ms: Command execution duration in milliseconds
        """
        self.durations.append(duration_ms)

    def get_min(self) -> float:
        """Get minimum duration in rolling window.

        Returns:
            Minimum duration in milliseconds, or 0.0 if no data
        """
        return min(self.durations) if self.durations else 0.0

    def get_mean(self) -> float:
        """Calculate mean of durations in rolling window.

        Returns:
            Mean duration in milliseconds, or 0.0 if no data
        """
        return sum(self.durations) / len(self.durations) if self.durations else 0.0

    def get_max(self) -> float:
        """Get maximum duration in rolling window.

        Returns:
            Maximum duration in milliseconds, or 0.0 if no data
        """
        return max(self.durations) if self.durations else 0.0

    def get_count(self) -> int:
        """Get number of recorded durations.

        Returns:
            Number of durations in rolling window
        """
        return len(self.durations)


class WorkerStatistics:
    """Aggregate statistics for all workers."""

    __slots__ = ("_stats",)

    def __init__(self):
        """Initialize statistics tracker."""
        self._stats: dict[str, WorkerStats] = {}

    def record_duration(self, command: str, duration_ms: float) -> None:
        """Record command execution duration.

        Args:
            command: Command that was executed
            duration_ms: Execution duration in milliseconds
        """
        if command not in self._stats:
            self._stats[command] = WorkerStats(command)
        self._stats[command].add_duration(duration_ms)

    def get_summary(self) -> str:
        """Generate summary report of all worker statistics.

        Returns:
            Formatted summary string with command durations and statistics
        """
        if not self._stats:
            return "No statistics available"

        lines = ["Worker Command Duration Statistics:", "=" * 80]

        for cmd, stats in self._stats.items():
            min_dur = stats.get_min()
            mean = stats.get_mean()
            max_dur = stats.get_max()
            count = stats.get_count()
            cmd_preview = cmd[:60] + "..." if len(cmd) > 60 else cmd
            lines.append(f"{cmd_preview}")
            lines.append(
                f"  Count: {count}, Min: {min_dur:.1f} ms, Mean: {mean:.1f} ms, Max: {max_dur:.1f} ms"
            )

        lines.append("=" * 80)
        return "\n".join(lines)
