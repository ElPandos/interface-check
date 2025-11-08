"""Statistics collection and analysis module for SUT platforms."""

from abc import ABC, abstractmethod
import contextlib
from dataclasses import dataclass, field
from datetime import datetime as dt, timedelta
import statistics as stats
from typing import Any


@dataclass(frozen=True)
class StatPoint:
    """Single statistics data point."""

    timestamp: dt
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StatSummary:
    """Statistical summary of data points."""

    count: int
    mean: float
    median: float
    min_value: float
    max_value: float
    std_dev: float
    percentile_95: float
    percentile_99: float


class StatCollector(ABC):
    """Abstract statistics collector interface."""

    @abstractmethod
    def collect(self) -> StatPoint:
        """Collect statistics data point."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Collector name."""


class NetworkStatCollector(StatCollector):
    """Network statistics collector."""

    def __init__(self, connection, interface: str):
        self._connection = connection
        self._interface = interface

    def collect(self) -> StatPoint:
        if not self._connection:
            return StatPoint(datetime.now(timezone.utc), 0.0)

        # Get RX/TX bytes
        rx_result = self._connection.execute_command(
            f"cat /sys/class/net/{self._interface}/statistics/rx_bytes"
        )
        tx_result = self._connection.execute_command(
            f"cat /sys/class/net/{self._interface}/statistics/tx_bytes"
        )

        rx_bytes = 0
        tx_bytes = 0

        if rx_result.success:
            with contextlib.suppress(ValueError):
                rx_bytes = int(rx_result.stdout.strip())

        if tx_result.success:
            with contextlib.suppress(ValueError):
                tx_bytes = int(tx_result.stdout.strip())

        total_bytes = rx_bytes + tx_bytes

        return StatPoint(
            timestamp=datetime.now(timezone.utc),
            value=float(total_bytes),
            metadata={"interface": self._interface, "rx_bytes": rx_bytes, "tx_bytes": tx_bytes},
        )

    @property
    def name(self) -> str:
        return f"network_{self._interface}"


class CpuStatCollector(StatCollector):
    """CPU statistics collector."""

    def __init__(self, connection):
        self._connection = connection

    def collect(self) -> StatPoint:
        if not self._connection:
            return StatPoint(datetime.now(timezone.utc), 0.0)

        result = self._connection.execute_command(
            "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print usage}'"
        )
        if result.success:
            try:
                cpu_usage = float(result.stdout.strip())
                return StatPoint(
                    timestamp=datetime.now(timezone.utc),
                    value=cpu_usage,
                    metadata={"unit": "percent"},
                )
            except ValueError:
                pass

        return StatPoint(datetime.now(timezone.utc), 0.0)

    @property
    def name(self) -> str:
        return "cpu_usage"


class MemoryStatCollector(StatCollector):
    """Memory statistics collector."""

    def __init__(self, connection):
        self._connection = connection

    def collect(self) -> StatPoint:
        if not self._connection:
            return StatPoint(datetime.now(timezone.utc), 0.0)

        result = self._connection.execute_command("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
        if result.success:
            try:
                mem_usage = float(result.stdout.strip())
                return StatPoint(
                    timestamp=datetime.now(timezone.utc),
                    value=mem_usage,
                    metadata={"unit": "percent"},
                )
            except ValueError:
                pass

        return StatPoint(datetime.now(timezone.utc), 0.0)

    @property
    def name(self) -> str:
        return "memory_usage"


class Statistics:
    """Independent statistics collection and analysis class."""

    def __init__(self, connection=None):
        self._connection = connection
        self._collectors: dict[str, StatCollector] = {}
        self._data: dict[str, list[StatPoint]] = {}
        self._max_points = 10000

    def add_collector(self, collector: StatCollector) -> None:
        """Add statistics collector."""
        self._collectors[collector.name] = collector
        if collector.name not in self._data:
            self._data[collector.name] = []

    def remove_collector(self, name: str) -> None:
        """Remove statistics collector."""
        self._collectors.pop(name, None)
        self._data.pop(name, None)

    def collect_all(self) -> dict[str, StatPoint]:
        """Collect data from all collectors."""
        results = {}
        for name, collector in self._collectors.items():
            try:
                point = collector.collect()
                results[name] = point

                # Add to data history
                if name not in self._data:
                    self._data[name] = []
                self._data[name].append(point)

                # Limit history size
                if len(self._data[name]) > self._max_points:
                    self._data[name].pop(0)

            except Exception:
                # Create error point
                results[name] = StatPoint(
                    timestamp=datetime.now(timezone.utc),
                    value=0.0,
                    metadata={"error": True},
                )

        return results

    def get_data(self, collector_name: str, hours: int = 24) -> list[StatPoint]:
        """Get data points for specific collector."""
        if collector_name not in self._data:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [p for p in self._data[collector_name] if p.timestamp > cutoff]

    def get_summary(self, collector_name: str, hours: int = 24) -> StatSummary | None:
        """Get statistical summary for collector."""
        data_points = self.get_data(collector_name, hours)
        if not data_points:
            return None

        values = [p.value for p in data_points]

        try:
            return StatSummary(
                count=len(values),
                mean=stats.mean(values),
                median=stats.median(values),
                min_value=min(values),
                max_value=max(values),
                std_dev=stats.stdev(values) if len(values) > 1 else 0.0,
                percentile_95=self._percentile(values, 95),
                percentile_99=self._percentile(values, 99),
            )
        except stats.StatisticsError:
            return None

    def get_trend(self, collector_name: str, hours: int = 24) -> str:
        """Get trend analysis for collector."""
        data_points = self.get_data(collector_name, hours)
        if len(data_points) < 2:
            return "insufficient_data"

        # Simple trend analysis using first and last values
        first_value = data_points[0].value
        last_value = data_points[-1].value

        change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0

        if abs(change_percent) < 5:
            return "stable"
        if change_percent > 0:
            return "increasing"
        return "decreasing"

    def get_anomalies(
        self, collector_name: str, hours: int = 24, threshold: float = 2.0
    ) -> list[StatPoint]:
        """Get anomalous data points (beyond threshold standard deviations)."""
        data_points = self.get_data(collector_name, hours)
        if len(data_points) < 3:
            return []

        values = [p.value for p in data_points]
        try:
            mean_val = stats.mean(values)
            std_val = stats.stdev(values)

            anomalies = []
            for point in data_points:
                if abs(point.value - mean_val) > threshold * std_val:
                    anomalies.append(point)

            return anomalies
        except stats.StatisticsError:
            return []

    def export_data(self, collector_name: str, hours: int = 24) -> dict[str, Any]:
        """Export data for external analysis."""
        data_points = self.get_data(collector_name, hours)
        summary = self.get_summary(collector_name, hours)
        trend = self.get_trend(collector_name, hours)
        anomalies = self.get_anomalies(collector_name, hours)

        return {
            "collector": collector_name,
            "time_range_hours": hours,
            "data_points": [
                {"timestamp": p.timestamp.isoformat(), "value": p.value, "metadata": p.metadata}
                for p in data_points
            ],
            "summary": {
                "count": summary.count,
                "mean": summary.mean,
                "median": summary.median,
                "min": summary.min_value,
                "max": summary.max_value,
                "std_dev": summary.std_dev,
                "percentile_95": summary.percentile_95,
                "percentile_99": summary.percentile_99,
            }
            if summary
            else None,
            "trend": trend,
            "anomalies": len(anomalies),
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def clear_data(self, collector_name: str | None = None) -> None:
        """Clear statistics data."""
        if collector_name:
            self._data.pop(collector_name, None)
        else:
            self._data.clear()

    def set_max_points(self, max_points: int) -> None:
        """Set maximum data points to keep."""
        self._max_points = max_points

        # Trim existing data
        for name in self._data:
            if len(self._data[name]) > max_points:
                self._data[name] = self._data[name][-max_points:]

    def get_collectors(self) -> list[str]:
        """Get list of collector names."""
        return list(self._collectors.keys())

    def _percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (percentile / 100.0) * (len(sorted_values) - 1)

        if index.is_integer():
            return sorted_values[int(index)]
        lower = sorted_values[int(index)]
        upper = sorted_values[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))
