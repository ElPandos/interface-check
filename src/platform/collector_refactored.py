"""Refactored data collector using new architecture."""

import logging
from typing import Any

from src.core import CollectionManager, CommandCollector, Result, Sample
from src.core.connection import Connection
from src.tools.ethtool import EthtoolTool

logger = logging.getLogger(__name__)


class EthtoolCollector(CommandCollector):
    """Ethtool-specific data collector."""

    def __init__(self, connection: Connection, interface: str):
        command = f"ethtool {interface}"
        source_name = f"ethtool-{interface}"
        super().__init__(connection, command, source_name)
        self._interface = interface
        self._ethtool = EthtoolTool(interface, None, None)  # Simplified for refactoring

    def collect(self) -> Result[dict[str, Any]]:
        """Collect ethtool data and parse it."""
        result = super().collect()
        if not result.success:
            return result

        try:
            # Parse ethtool output
            parsed_data = self._parse_ethtool_output(result.data)
            return Result.ok(parsed_data)
        except Exception as e:
            return Result.fail(f"Failed to parse ethtool output: {e}")

    def _parse_ethtool_output(self, output: str) -> dict[str, Any]:
        """Parse ethtool command output."""
        data = {
            "interface": self._interface,
            "speed": "Unknown",
            "duplex": "Unknown",
            "link_detected": False,
            "raw_output": output,
        }

        for raw_line in output.split("\n"):
            line = raw_line.strip()
            if "Speed:" in line:
                data["speed"] = line.split("Speed:")[1].strip()
            elif "Duplex:" in line:
                data["duplex"] = line.split("Duplex:")[1].strip()
            elif "Link detected:" in line:
                data["link_detected"] = "yes" in line.lower()

        return data


class NetworkStatsCollector(CommandCollector):
    """Network statistics collector."""

    def __init__(self, connection: Connection, interface: str):
        command = f"cat /proc/net/dev | grep {interface}"
        source_name = f"netstats-{interface}"
        super().__init__(connection, command, source_name)
        self._interface = interface

    def collect(self) -> Result[dict[str, Any]]:
        """Collect network statistics."""
        result = super().collect()
        if not result.success:
            return result

        try:
            parsed_data = self._parse_net_stats(result.data)
            return Result.ok(parsed_data)
        except Exception as e:
            return Result.fail(f"Failed to parse network stats: {e}")

    def _parse_net_stats(self, output: str) -> dict[str, Any]:
        """Parse /proc/net/dev output."""
        data = {
            "interface": self._interface,
            "rx_bytes": 0,
            "tx_bytes": 0,
            "rx_packets": 0,
            "tx_packets": 0,
            "rx_errors": 0,
            "tx_errors": 0,
        }

        for line in output.split("\n"):
            if self._interface in line:
                parts = line.split()
                if len(parts) >= 17:
                    data.update(
                        {
                            "rx_bytes": int(parts[1]),
                            "rx_packets": int(parts[2]),
                            "rx_errors": int(parts[3]),
                            "tx_bytes": int(parts[9]),
                            "tx_packets": int(parts[10]),
                            "tx_errors": int(parts[11]),
                        }
                    )
                break

        return data


class SystemStatsCollector(CommandCollector):
    """System statistics collector."""

    def __init__(self, connection: Connection):
        command = "cat /proc/loadavg && free -m && df -h /"
        source_name = "system-stats"
        super().__init__(connection, command, source_name)

    def collect(self) -> Result[dict[str, Any]]:
        """Collect system statistics."""
        result = super().collect()
        if not result.success:
            return result

        try:
            parsed_data = self._parse_system_stats(result.data)
            return Result.ok(parsed_data)
        except Exception as e:
            return Result.fail(f"Failed to parse system stats: {e}")

    def _parse_system_stats(self, output: str) -> dict[str, Any]:
        """Parse system statistics output."""
        lines = output.strip().split("\n")
        data = {"load_avg": [0.0, 0.0, 0.0], "memory_total": 0, "memory_used": 0, "memory_free": 0, "disk_usage": "0%"}

        # Parse load average
        if lines:
            load_parts = lines[0].split()
            if len(load_parts) >= 3:
                data["load_avg"] = [float(load_parts[0]), float(load_parts[1]), float(load_parts[2])]

        # Parse memory info
        for line in lines:
            if line.startswith("Mem:"):
                mem_parts = line.split()
                if len(mem_parts) >= 4:
                    data.update(
                        {
                            "memory_total": int(mem_parts[1]),
                            "memory_used": int(mem_parts[2]),
                            "memory_free": int(mem_parts[3]),
                        }
                    )
            elif "/" in line and "%" in line:
                # Parse disk usage
                parts = line.split()
                if len(parts) >= 5:
                    data["disk_usage"] = parts[4]

        return data


class RefactoredCollectionService:
    """Refactored collection service using new architecture."""

    def __init__(self):
        self._manager = CollectionManager()
        self._active_collectors: dict[str, str] = {}  # collector_id -> source_name

    def initialize(self) -> Result[None]:
        """Initialize collection service."""
        return self._manager.initialize()

    def cleanup(self) -> None:
        """Cleanup collection service."""
        self._manager.cleanup()

    def add_ethtool_collector(self, connection: Connection, interface: str, interval: float = 5.0) -> Result[str]:
        """Add ethtool collector for interface."""
        collector = EthtoolCollector(connection, interface)
        result = self._manager.add_collector(collector, interval)

        if result.success:
            collector_id = f"ethtool-{interface}"
            self._active_collectors[collector_id] = result.data

            # Start collection
            start_result = self._manager.start_collector(result.data)
            if not start_result.success:
                self._manager.remove_collector(result.data)
                return start_result

        return result

    def add_network_stats_collector(self, connection: Connection, interface: str, interval: float = 1.0) -> Result[str]:
        """Add network statistics collector."""
        collector = NetworkStatsCollector(connection, interface)
        result = self._manager.add_collector(collector, interval)

        if result.success:
            collector_id = f"netstats-{interface}"
            self._active_collectors[collector_id] = result.data

            # Start collection
            start_result = self._manager.start_collector(result.data)
            if not start_result.success:
                self._manager.remove_collector(result.data)
                return start_result

        return result

    def add_system_stats_collector(self, connection: Connection, interval: float = 10.0) -> Result[str]:
        """Add system statistics collector."""
        collector = SystemStatsCollector(connection)
        result = self._manager.add_collector(collector, interval)

        if result.success:
            collector_id = "system-stats"
            self._active_collectors[collector_id] = result.data

            # Start collection
            start_result = self._manager.start_collector(result.data)
            if not start_result.success:
                self._manager.remove_collector(result.data)
                return start_result

        return result

    def remove_collector(self, collector_id: str) -> Result[None]:
        """Remove collector by ID."""
        if collector_id not in self._active_collectors:
            return Result.fail(f"Collector {collector_id} not found")

        source_name = self._active_collectors[collector_id]
        result = self._manager.remove_collector(source_name)

        if result.success:
            del self._active_collectors[collector_id]

        return result

    def get_samples(self, collector_id: str, max_count: int | None = None) -> list[Sample]:
        """Get samples from specific collector."""
        if collector_id not in self._active_collectors:
            return []

        source_name = self._active_collectors[collector_id]
        return self._manager.get_samples(source_name, max_count)

    def get_all_samples(self) -> dict[str, list[Sample]]:
        """Get samples from all collectors."""
        all_samples = self._manager.get_all_samples()

        # Map source names back to collector IDs
        result = {}
        for collector_id, source_name in self._active_collectors.items():
            if source_name in all_samples:
                result[collector_id] = all_samples[source_name]

        return result

    def get_statistics(self) -> dict[str, dict[str, Any]]:
        """Get statistics for all collectors."""
        all_stats = self._manager.get_statistics()

        # Map source names back to collector IDs
        result = {}
        for collector_id, source_name in self._active_collectors.items():
            if source_name in all_stats:
                result[collector_id] = all_stats[source_name]

        return result

    def start_all(self) -> None:
        """Start all collectors."""
        self._manager.start_all()

    def stop_all(self) -> None:
        """Stop all collectors."""
        self._manager.stop_all()

    def get_active_collectors(self) -> list[str]:
        """Get list of active collector IDs."""
        return list(self._active_collectors.keys())
