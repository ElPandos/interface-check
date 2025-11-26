"""Worker statistics tracking and reporting."""

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.core.cli import PrettyFrame


@dataclass
class WorkerStats:
    """Statistics for a single worker.

    Tracks command execution durations with rolling mean of last 20 executions.
    """

    command: str
    durations: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    send_times: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    read_times: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    cycle_times: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    parsed_times: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    timestamps: deque[float] = field(default_factory=lambda: deque(maxlen=20))
    max_samples: int = 20

    def add_duration(
        self,
        duration_ms: float,
        send_ms: float = 0.0,
        read_ms: float = 0.0,
        cycle_ms: float = 0.0,
        parsed_ms: float = 0.0,
        timestamp: float = 0.0,
    ) -> None:
        """Add command duration to rolling window.

        Args:
            duration_ms: Command execution duration in milliseconds
            send_ms: Time to send command in milliseconds
            read_ms: Time to read response in milliseconds
            cycle_ms: Total cycle time in milliseconds
            parsed_ms: Parsed execution time from time command in milliseconds
            timestamp: Unix timestamp when measurement was taken
        """
        self.durations.append(duration_ms)
        if send_ms > 0:
            self.send_times.append(send_ms)
        if read_ms > 0:
            self.read_times.append(read_ms)
        if cycle_ms > 0:
            self.cycle_times.append(cycle_ms)
        if parsed_ms > 0:
            self.parsed_times.append(parsed_ms)
        if timestamp > 0:
            self.timestamps.append(timestamp)

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

    def get_median(self) -> float:
        """Calculate median of durations in rolling window.

        For even-length lists, returns mean of two center values.

        Returns:
            Median duration in milliseconds, or 0.0 if no data
        """
        if not self.durations:
            return 0.0

        sorted_durations = sorted(self.durations)
        n = len(sorted_durations)

        if n % 2 == 1:
            return sorted_durations[n // 2]
        mid1 = sorted_durations[n // 2 - 1]
        mid2 = sorted_durations[n // 2]
        return (mid1 + mid2) / 2.0


class WorkerStatistics:
    """Aggregate statistics for all workers."""

    __slots__ = ("_stats",)

    def __init__(self):
        """Initialize statistics tracker."""
        self._stats: dict[str, WorkerStats] = {}

    def record_duration(
        self,
        command: str,
        duration_ms: float,
        send_ms: float = 0.0,
        read_ms: float = 0.0,
        cycle_ms: float = 0.0,
        parsed_ms: float = 0.0,
        timestamp: float = 0.0,
    ) -> None:
        """Record command execution duration.

        Args:
            command: Command that was executed
            duration_ms: Execution duration in milliseconds
            send_ms: Time to send command in milliseconds
            read_ms: Time to read response in milliseconds
            cycle_ms: Total cycle time in milliseconds
            parsed_ms: Parsed execution time from time command in milliseconds
            timestamp: Unix timestamp when measurement was taken
        """
        if command not in self._stats:
            self._stats[command] = WorkerStats(command)
        self._stats[command].add_duration(
            duration_ms, send_ms, read_ms, cycle_ms, parsed_ms, timestamp
        )

    def get_summary(self) -> str:
        """Generate summary report of all worker statistics.

        Returns:
            Formatted summary string with command durations and statistics
        """
        if not self._stats:
            return "No statistics available"

        frame = PrettyFrame(width=80)
        rows = []

        # Sort commands alphabetically for consistent display
        for cmd, stats in sorted(self._stats.items()):
            min_dur = stats.get_min()
            mean = stats.get_mean()
            median = stats.get_median()
            max_dur = stats.get_max()
            count = stats.get_count()

            # Calculate averages
            send_avg = sum(stats.send_times) / len(stats.send_times) if stats.send_times else 0.0
            read_avg = sum(stats.read_times) / len(stats.read_times) if stats.read_times else 0.0
            cycle_avg = (
                sum(stats.cycle_times) / len(stats.cycle_times) if stats.cycle_times else 0.0
            )
            parsed_avg = (
                sum(stats.parsed_times) / len(stats.parsed_times) if stats.parsed_times else 0.0
            )
            delay = cycle_avg - mean if cycle_avg > 0 else 0.0

            # Command header
            cmd_preview = f"'{cmd[:72]}...'" if len(cmd) > 72 else f"'{cmd}'"
            rows.append(f"Command: {cmd_preview}")
            rows.append("---")
            rows.append(f"Max avg. count no: {count} │ Manual delay: {delay:7.3f} ms")
            rows.append("---")
            rows.append(f"Min:  {min_dur:10.3f} ms │ Max:  {max_dur:10.3f} ms")
            rows.append(f"Avg:  {mean:10.3f} ms │ Median: {median:8.3f} ms")
            rows.append(f"Send: {send_avg:10.3f} ms │ Read: {read_avg:10.3f} ms")
            rows.append(f"Cycle: {cycle_avg:9.3f} ms │ Time:   {parsed_avg:8.3f} ms")
            rows.append("---")

        # Add metric descriptions once at the end
        rows.append("Metric Descriptions:")
        rows.append("  Max avg. count no: Number of samples in rolling window")
        rows.append("  Manual delay: Sleep time between executions (Cycle - Avg)")
        rows.append("  Min/Max: Fastest and slowest command execution times")
        rows.append("  Avg: Mean execution time across all samples")
        rows.append("  Median: Middle value of sorted execution times")
        rows.append("  Send: Average time to send command over SSH connection")
        rows.append("  Read: Average time to read response from SSH connection")
        rows.append("  Cycle: Total time per iteration (Avg + Manual delay)")
        rows.append("  Time: Real execution time on remote system (from 'time' cmd)")
        rows.append("---")
        rows.append("Max Duration Analysis:")
        # Sort commands alphabetically for consistent display
        for cmd, stats in sorted(self._stats.items()):
            if not stats.durations:
                continue
            max_val = stats.get_max()
            max_idx = list(stats.durations).index(max_val)
            cmd_preview = f"'{cmd[:60]}...'" if len(cmd) > 60 else f"'{cmd}'"
            rows.append(f"  {cmd_preview}")
            rows.append(f"    Max: {max_val:.3f} ms")
            if stats.timestamps and max_idx < len(stats.timestamps):
                ts = list(stats.timestamps)[max_idx]
                dt = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                rows.append(f"    Timestamp: {dt}")
            if stats.parsed_times and max_idx < len(stats.parsed_times):
                rows.append(f"    Parsed time at max: {list(stats.parsed_times)[max_idx]:.3f} ms")

        return frame.build("Worker Command Duration Statistics", rows)
