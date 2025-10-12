"""Hardware management module for SUT platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CpuInfo:
    """CPU information structure."""

    architecture: str = "unknown"
    cores: int = 0
    model: str = "unknown"
    frequency: float = 0.0
    cache_size: str = "unknown"


@dataclass(frozen=True)
class MemoryInfo:
    """Memory information structure."""

    total: int = 0
    available: int = 0
    used: int = 0
    free: int = 0
    usage_percent: float = 0.0


@dataclass(frozen=True)
class StorageInfo:
    """Storage device information."""

    device: str = ""
    size: int = 0
    used: int = 0
    available: int = 0
    usage_percent: float = 0.0
    filesystem: str = "unknown"


@dataclass(frozen=True)
class NetworkInterface:
    """Network interface information."""

    name: str = ""
    mac_address: str = ""
    ip_address: str = ""
    state: str = "unknown"
    speed: str = "unknown"
    duplex: str = "unknown"


class HardwareProbe(ABC):
    """Abstract hardware probe interface."""

    @abstractmethod
    def probe(self) -> Any:
        """Probe hardware component."""


class Hardware:
    """Independent hardware management class."""

    def __init__(self, connection=None):
        self._connection = connection
        self._probes: dict[str, HardwareProbe] = {}
        self._cache: dict[str, Any] = {}

    def get_cpu_info(self) -> CpuInfo:
        """Get CPU information."""
        if "cpu" in self._cache:
            return self._cache["cpu"]

        if not self._connection:
            return CpuInfo()

        result = self._connection.execute_command("lscpu")
        if not result.success:
            return CpuInfo()

        data = self._parse_key_value(result.stdout)
        cpu_info = CpuInfo(
            architecture=data.get("Architecture", "unknown"),
            cores=int(data.get("CPU(s)", "0")),
            model=data.get("Model name", "unknown"),
            frequency=self._parse_frequency(data.get("CPU MHz", "0")),
            cache_size=data.get("L3 cache", "unknown"),
        )

        self._cache["cpu"] = cpu_info
        return cpu_info

    def get_memory_info(self) -> MemoryInfo:
        """Get memory information."""
        if not self._connection:
            return MemoryInfo()

        result = self._connection.execute_command("free -b")
        if not result.success:
            return MemoryInfo()

        lines = result.stdout.strip().split("\n")
        if len(lines) < 2:
            return MemoryInfo()

        mem_line = lines[1].split()
        if len(mem_line) < 7:
            return MemoryInfo()

        total = int(mem_line[1])
        used = int(mem_line[2])
        free = int(mem_line[3])
        available = int(mem_line[6]) if len(mem_line) > 6 else free

        return MemoryInfo(
            total=total,
            used=used,
            free=free,
            available=available,
            usage_percent=(used / total * 100) if total > 0 else 0.0,
        )

    def get_storage_info(self) -> list[StorageInfo]:
        """Get storage information for all mounted filesystems."""
        if not self._connection:
            return []

        result = self._connection.execute_command("df -B1")
        if not result.success:
            return []

        storage_list = []
        lines = result.stdout.strip().split("\n")[1:]  # Skip header

        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    size = int(parts[1])
                    used = int(parts[2])
                    available = int(parts[3])
                    usage_percent = float(parts[4].rstrip("%"))

                    storage_list.append(
                        StorageInfo(
                            device=parts[0],
                            size=size,
                            used=used,
                            available=available,
                            usage_percent=usage_percent,
                            filesystem=parts[5] if len(parts) > 5 else "unknown",
                        )
                    )
                except (ValueError, IndexError):
                    continue

        return storage_list

    def get_network_interfaces(self) -> list[NetworkInterface]:
        """Get network interface information."""
        if not self._connection:
            return []

        interfaces = []

        # Get interface list
        result = self._connection.execute_command("ls /sys/class/net/")
        if not result.success:
            return []

        interface_names = result.stdout.strip().split()

        for name in interface_names:
            if not name.strip():
                continue

            interface = NetworkInterface(name=name)

            # Get MAC address
            mac_result = self._connection.execute_command(f"cat /sys/class/net/{name}/address")
            if mac_result.success:
                interface = interface.__class__(
                    name=interface.name,
                    mac_address=mac_result.stdout.strip(),
                    ip_address=interface.ip_address,
                    state=interface.state,
                    speed=interface.speed,
                    duplex=interface.duplex,
                )

            # Get state
            state_result = self._connection.execute_command(f"cat /sys/class/net/{name}/operstate")
            if state_result.success:
                interface = interface.__class__(
                    name=interface.name,
                    mac_address=interface.mac_address,
                    ip_address=interface.ip_address,
                    state=state_result.stdout.strip(),
                    speed=interface.speed,
                    duplex=interface.duplex,
                )

            interfaces.append(interface)

        return interfaces

    def get_temperature_sensors(self) -> dict[str, float]:
        """Get temperature from available sensors."""
        sensors = {}

        if not self._connection:
            return sensors

        # CPU thermal zones
        for i in range(10):  # Check up to 10 thermal zones
            result = self._connection.execute_command(f"cat /sys/class/thermal/thermal_zone{i}/temp")
            if result.success:
                try:
                    temp = float(result.stdout.strip()) / 1000.0
                    sensors[f"thermal_zone{i}"] = temp
                except ValueError:
                    continue
            else:
                break

        # Try sensors command if available
        result = self._connection.execute_command("sensors")
        if result.success:
            for line in result.stdout.split("\n"):
                if "°C" in line and ":" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        name = parts[0].strip()
                        temp_part = parts[1].split("°C")[0].strip()
                        try:
                            temp = float(temp_part.split()[-1])
                            sensors[name] = temp
                        except (ValueError, IndexError):
                            continue

        return sensors

    def add_probe(self, name: str, probe: HardwareProbe) -> None:
        """Add custom hardware probe."""
        self._probes[name] = probe

    def run_probe(self, name: str) -> Any:
        """Run specific hardware probe."""
        if name in self._probes:
            return self._probes[name].probe()
        return None

    def clear_cache(self) -> None:
        """Clear hardware information cache."""
        self._cache.clear()

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    def _parse_frequency(self, freq_str: str) -> float:
        """Parse frequency string to float."""
        try:
            return float(freq_str)
        except ValueError:
            return 0.0
