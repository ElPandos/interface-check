"""Health monitoring module for SUT platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime as dt, timedelta

from src.core.connect import SshConnection


@dataclass(frozen=True)
class HealthMetric:
    """Individual health metric."""

    name: str
    value: float
    unit: str = ""
    threshold_min: float | None = None
    threshold_max: float | None = None
    status: str = "ok"  # ok, warning, critical
    timestamp: dt = field(default_factory=lambda: dt.now(UTC))


@dataclass(frozen=True)
class HealthSnapshot:
    """Complete health snapshot at a point in time."""

    timestamp: dt
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    temperature: float = 0.0
    load_average: float = 0.0
    network_errors: int = 0
    custom_metrics: dict[str, float] = field(default_factory=dict)


class HealthMonitor(ABC):
    """Abstract health monitor interface."""

    @abstractmethod
    def collect(self) -> HealthMetric:
        """Collect health metric.

        Returns:
            Health metric
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Monitor name.

        Returns:
            Monitor name
        """


class CpuMonitor(HealthMonitor):
    """CPU usage monitor."""

    def __init__(self, ssh_connection: SshConnection):
        """Initialize CPU monitor.

        Args:
            ssh_connection: SSH connection
        """
        self._ssh_connection = ssh_connection

    def collect(self) -> HealthMetric:
        """Collect CPU metric.

        Returns:
            CPU health metric
        """
        if not self._ssh_connection:
            return HealthMetric("cpu_usage", 0.0, "%")

        result = self._ssh_connection.execute_command(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
        )
        if result.success:
            try:
                usage = float(result.str_out.strip())
                status = "ok"
                if usage > 90:
                    status = "critical"
                elif usage > 75:
                    status = "warning"

                return HealthMetric(
                    name="cpu_usage", value=usage, unit="%", threshold_max=90.0, status=status
                )
            except ValueError:
                pass

        return HealthMetric("cpu_usage", 0.0, "%")

    @property
    def name(self) -> str:
        """Get monitor name.

        Returns:
            Monitor name
        """
        return "cpu_monitor"


class MemoryMonitor(HealthMonitor):
    """Memory usage monitor."""

    def __init__(self, ssh_connection: SshConnection):
        """Initialize memory monitor.

        Args:
            ssh_connection: SSH connection
        """
        self._ssh_connection = ssh_connection

    def collect(self) -> HealthMetric:
        """Collect memory metric.

        Returns:
            Memory health metric
        """
        if not self._ssh_connection:
            return HealthMetric("memory_usage", 0.0, "%")

        result = self._ssh_connection.execute_command(
            "free | grep Mem | awk '{print ($3/$2) * 100.0}'"
        )
        if result.success:
            try:
                usage = float(result.str_out.strip())
                status = "ok"
                if usage > 95:
                    status = "critical"
                elif usage > 85:
                    status = "warning"

                return HealthMetric(
                    name="memory_usage", value=usage, unit="%", threshold_max=95.0, status=status
                )
            except ValueError:
                pass

        return HealthMetric("memory_usage", 0.0, "%")

    @property
    def name(self) -> str:
        return "memory_monitor"


class TemperatureMonitor(HealthMonitor):
    """Temperature monitor."""

    def __init__(
        self,
        ssh_connection: SshConnection,
        sensor_path: str = "/sys/class/thermal/thermal_zone0/temp",
    ):
        """Initialize temperature monitor.

        Args:
            ssh_connection: SSH connection
            sensor_path: Path to temperature sensor
        """
        self._ssh_connection = ssh_connection
        self._sensor_path = sensor_path

    def collect(self) -> HealthMetric:
        """Collect temperature metric.

        Returns:
            Temperature health metric
        """
        if not self._ssh_connection:
            return HealthMetric("temperature", 0.0, "°C")

        result = self._ssh_connection.execute_command(f"cat {self._sensor_path}")
        if result.success:
            try:
                temp = float(result.str_out.strip()) / 1000.0
                status = "ok"
                if temp > 85:
                    status = "critical"
                elif temp > 75:
                    status = "warning"

                return HealthMetric(
                    name="temperature", value=temp, unit="°C", threshold_max=85.0, status=status
                )
            except ValueError:
                pass

        return HealthMetric("temperature", 0.0, "°C")

    @property
    def name(self) -> str:
        return "temperature_monitor"


class Health:
    """Independent health monitoring class."""

    def __init__(self, ssh_connection: SshConnection = None):
        """Initialize health monitor.

        Args:
            ssh_connection: SSH connection
        """
        self._ssh_connection = ssh_connection
        self._monitors: dict[str, HealthMonitor] = {}
        self._history: list[HealthSnapshot] = []
        self._max_history = 1000
        self._setup_default_monitors()

    def _setup_default_monitors(self):
        """Setup default health monitors."""
        if not self._ssh_connection:
            return

        self._monitors["cpu"] = CpuMonitor(self._ssh_connection)
        self._monitors["memory"] = MemoryMonitor(self._ssh_connection)
        self._monitors["temperature"] = TemperatureMonitor(self._ssh_connection)

    def add_monitor(self, monitor: HealthMonitor) -> None:
        """Add custom health monitor.

        Args:
            monitor: Health monitor instance
        """
        self._monitors[monitor.name] = monitor

    def remove_monitor(self, name: str) -> None:
        """Remove health monitor.

        Args:
            name: Monitor name
        """
        self._monitors.pop(name, None)

    def collect_metrics(self) -> dict[str, HealthMetric]:
        """Collect all health metrics.

        Returns:
            Dictionary of metrics
        """
        metrics = {}
        for name, monitor in self._monitors.items():
            try:
                metric = monitor.collect()
                metrics[name] = metric
            except Exception:
                # Create error metric
                metrics[name] = HealthMetric(name=name, value=0.0, status="error")
        return metrics

    def collect_snapshot(self) -> HealthSnapshot:
        """Collect complete health snapshot.

        Returns:
            Health snapshot
        """
        metrics = self.collect_metrics()

        snapshot = HealthSnapshot(
            timestamp=dt.now(UTC),
            cpu_usage=metrics.get("cpu", HealthMetric("cpu", 0.0)).value,
            memory_usage=metrics.get("memory", HealthMetric("memory", 0.0)).value,
            temperature=metrics.get("temperature", HealthMetric("temperature", 0.0)).value,
            load_average=self._get_load_average(),
            network_errors=self._get_network_errors(),
            custom_metrics={
                name: metric.value
                for name, metric in metrics.items()
                if name not in ["cpu", "memory", "temperature"]
            },
        )

        # Add to history
        self._history.append(snapshot)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        return snapshot

    def get_history(self, hours: int = 24) -> list[HealthSnapshot]:
        """Get health history for specified hours.

        Args:
            hours: Number of hours

        Returns:
            List of health snapshots
        """
        cutoff = dt.now(UTC) - timedelta(hours=hours)
        return [h for h in self._history if h.timestamp > cutoff]

    def get_latest_snapshot(self) -> HealthSnapshot | None:
        """Get most recent health snapshot.

        Returns:
            Latest snapshot or None
        """
        return self._history[-1] if self._history else None

    def get_health_status(self) -> str:
        """Get overall health status.

        Returns:
            Health status string
        """
        metrics = self.collect_metrics()

        critical_count = sum(1 for m in metrics.values() if m.status == "critical")
        warning_count = sum(1 for m in metrics.values() if m.status == "warning")

        if critical_count > 0:
            return "critical"
        if warning_count > 0:
            return "warning"
        return "healthy"

    def get_alerts(self) -> list[HealthMetric]:
        """Get current health alerts.

        Returns:
            List of alert metrics
        """
        metrics = self.collect_metrics()
        return [m for m in metrics.values() if m.status in ["warning", "critical"]]

    def clear_history(self) -> None:
        """Clear health history."""
        self._history.clear()

    def set_max_history(self, max_entries: int) -> None:
        """Set maximum history entries.

        Args:
            max_entries: Maximum number of entries
        """
        self._max_history = max_entries
        if len(self._history) > max_entries:
            self._history = self._history[-max_entries:]

    def _get_load_average(self) -> float:
        """Get system load average."""
        if not self._ssh_connection:
            return 0.0

        result = self._ssh_connection.execute_command(
            "uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//'"
        )
        if result.success:
            try:
                return float(result.str_out.strip())
            except ValueError:
                pass
        return 0.0

    def _get_network_errors(self) -> int:
        """Get network error count."""
        if not self._ssh_connection:
            return 0

        result = self._ssh_connection.execute_command(
            "cat /proc/net/dev | awk 'NR>2 {sum+=$4+$12} END {print sum}'"
        )
        if result.success:
            try:
                return int(result.str_out.strip())
            except ValueError:
                pass
        return 0
