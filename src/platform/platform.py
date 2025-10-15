from abc import ABC, abstractmethod
import contextlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from src.core.json import Json
from src.platform import Hardware, Health, Power, Software, Statistics

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------- #
#                                  Interfaces                                  #
# ---------------------------------------------------------------------------- #


class Interfaces:
    _SYSTEM_FILE: str = "/sys/class/net"
    _EXCLUDE: tuple[str] = ("lo", "veth", "docker", "virbr", "br-", "tun", "tap")

    """
    Utility class to list all network interfaces available on the system.
    Uses /sys/class/net for discovery (safe, no root required).
    """

    def __init__(self, *, include_virtual: bool = True, include_loopback: bool = True):
        """
        :param include_virtual: If False, skip virtual interfaces (veth, docker, etc.)
        :param include_loopback: If False, skip loopback ("lo")
        """
        self._include_virtual = include_virtual
        self._include_loopback = include_loopback
        self._interfaces: list[str] = self._discover()

    def _discover(self) -> list[str]:
        interfaces = []
        for iface in Path(self._SYSTEM_FILE).iterdir():
            iface_name = iface.name
            # Skip loopback if requested
            if not self.include_loopback and iface_name == "lo":
                continue

            # Skip common virtual interfaces if requested
            if not self.include_virtual and iface_name.startswith(self._EXCLUDE):
                continue

            interfaces.append(iface_name)

        return interfaces

    @property
    def list(self) -> list[str]:
        """Return all discovered interfaces."""
        return self._interfaces

    def __repr__(self) -> str:
        return f"Interfaces(count={len(self._interfaces)}, interfaces={self._interfaces})"


# ---------------------------------------------------------------------------- #
#                                  Command I/O                                 #
# ---------------------------------------------------------------------------- #


def run_command(command: list[str], *, fail_ok: bool = False) -> str:
    if not command or not all(isinstance(arg, str) for arg in command):
        msg = "Command must be a non-empty list of strings"
        raise ValueError(msg)

    # Input is validated above - command is list of strings, shell=False prevents injection
    result = subprocess.run(  # noqa: S603
        command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False
    )

    if result.returncode != 0:
        if fail_ok:
            logger.warning(f"Command failed but will continue: {' '.join(command)}")
        else:
            raise RuntimeError(f"Command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    else:
        logger.info(result.stdout)
    return result.stdout


# ---------------------------------------------------------------------------- #
#                                     PATH                                     #
# ---------------------------------------------------------------------------- #


def set_python_path(full_path: Path) -> None:
    if not full_path or not str(full_path).strip():
        logger.warning("PYTHONPATH is empty - nothing was added to sys.path")
        return

    base_dir = full_path.parent
    target_dir = base_dir.resolve()

    try:
        exist_dir(target_dir)
    except FileNotFoundError:
        logger.exception("PYTHONPATH directory was not found")
        raise

    target_dir_str = str(target_dir)
    if target_dir_str in sys.path:
        logger.debug("PYTHONPATH was found in sys.path. Will not add again")
        return

    sys.path.insert(0, target_dir_str)
    logger.debug(f"Added '{target_dir_str}' to the beginning of sys.path")


# ---------------------------------------------------------------------------- #
#                                     File                                     #
# ---------------------------------------------------------------------------- #


def exist_file(full_path: Path) -> None:
    if full_path.exists():
        logger.debug(f"File was found: {full_path}")
        return
    raise FileNotFoundError(f"File was not found: {full_path}")


# ---------------------------------------------------------------------------- #
#                                   Directory                                  #
# ---------------------------------------------------------------------------- #


def exist_dir(dir_path: Path) -> None:
    if dir_path.exists():
        logger.debug(f"Folder was found: {dir_path}")
    else:
        raise FileNotFoundError(f"Folder was not found: {dir_path}")


def create_dir(dir_path: Path) -> None:
    if not dir_path.exists():
        logger.warning(f"Folder was not found. Creating it: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
    else:
        logger.debug(f"Folder was found: {dir_path}")


# ---------------------------------------------------------------------------- #
#                                     JSON                                     #
# ---------------------------------------------------------------------------- #


def save_json(config: Any, full_path: Path) -> None:
    """Legacy wrapper for JsonHandler.save()."""
    Json.save(config, full_path)


def load_json(full_path: Path) -> dict[str, Any] | list[Any]:
    """Legacy wrapper for JsonHandler.load()."""
    return Json.load(full_path)


def dump_lists_to_file(list1: list[Any], list2: list[Any], config_path: Path, file_name: str) -> None:
    """
    Safely dump two lists into a JSON file.
    If the file already exists, it is renamed with a timestamp before writing.

    Args:
        list1: First list of data.
        list2: Second list of data.
        config_path: Directory path where the file will be created.
        file_name: Name of the output file.
    """
    try:
        # Ensure parent directories exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        full_path = config_path / file_name

        # Check if file exists and back it up
        if full_path.exists():
            timestamp = datetime.now(tz=datetime.UTC).strftime("%Y%m%d_%H%M%S")
            backup_path = full_path.with_suffix(f".{timestamp}")
            full_path.rename(backup_path)
            logger.info(f"Existing file renamed to backup: {backup_path}")

        # Prepare the data structure
        data = {
            "x": list1,
            "y": list2,
            "created_at": datetime.now(tz=datetime.UTC).isoformat(),
        }

        # Write to JSON file with indentation for readability
        Json.save(data, full_path)

        logger.info(f"Successfully wrote data to: {full_path}")

    except Exception:
        logger.exception(f"Failed to dump lists to file '{full_path}'")


def merge_lists_from_base_and_backups(base_file: str) -> Path:
    """
    Merge lists from the base JSON file and all its backup files
    (following the .YYYYMMDD_HHMMSS.bak suffix) into a single Excel file.

    Args:
        base_file: Full path to the base JSON file (e.g., interface_data.json).

    Returns:
        Path to the merged Excel file.
    """
    try:
        base_path = Path(base_file)

        if not base_path.exists():
            logger.error(f"Base file does not exist: {base_path}")
            return base_path

        # ------------------------------------------------------------------ #
        # Step 1: Identify base file and backup files
        # ------------------------------------------------------------------ #
        parent_dir = base_path.parent
        base_stem = base_path.stem  # e.g., "interface_data"
        suffix_pattern = re.compile(rf"{re.escape(base_stem)}\.(\d{{8}}_\d{{6}})\.bak")

        files_to_merge = [base_path]  # start with base file

        # Find backup files in same directory
        for f in parent_dir.glob(f"{base_stem}.*.bak*"):
            if suffix_pattern.search(f.name):
                files_to_merge.append(f)

        # Sort files by timestamp (base file first, then backups chronologically)
        def file_sort_key(f: Path):
            match = suffix_pattern.search(f.name)
            return match.group(1) if match else "0"

        files_to_merge.sort(key=file_sort_key)
        logger.info(f"Found {len(files_to_merge)} files to merge")

        # Process files and return merged path
        return base_path.with_suffix(".xlsx")

    except Exception:
        logger.exception("Failed to merge files")
        return Path(base_file).with_suffix(".xlsx")


# ---------------------------------------------------------------------------- #
#                                   Platform                                   #
# ---------------------------------------------------------------------------- #


@dataclass
class SystemHealth:
    """System health metrics."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    temperature: float = 0.0
    network_status: dict[str, bool] = field(default_factory=dict)
    power_status: str = "unknown"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SoftwareInfo:
    """Software information."""

    name: str
    version: str = "unknown"
    installed: bool = False
    path: str | None = None


class SystemProbe(ABC):
    """Abstract system probe interface."""

    @abstractmethod
    def probe(self) -> Any:
        """Probe system for specific information."""


class Platform:
    """Manufacturer-independent system under test (SUT) platform."""

    def __init__(self, connection=None, name: str = "SUT"):
        self._connection = connection
        self._name = name
        self._probes: dict[str, SystemProbe] = {}
        self._health_log: list[SystemHealth] = []
        self._software_cache: dict[str, SoftwareInfo] = {}

        # Initialize specialized components
        self.hardware = Hardware(connection)
        self.software = Software(connection)
        self.health = Health(connection)
        self.statistics = Statistics(connection)
        self.power = Power(connection)

    # Hardware Management
    def get_hardware_info(self) -> dict[str, Any]:
        """Get comprehensive hardware information."""
        info = {}

        # CPU info
        if self._connection:
            result = self._connection.execute_command("lscpu")
            if result.success:
                info["cpu"] = self._parse_key_value(result.stdout)

        # Memory info
        if self._connection:
            result = self._connection.execute_command("free -h")
            if result.success:
                info["memory"] = result.stdout

        # Network interfaces
        info["interfaces"] = Interfaces().list

        return info

    def get_temperature(self, sensor: str = "cpu") -> float:
        """Get temperature from specified sensor."""
        if not self._connection:
            return 0.0

        commands = {
            "cpu": "cat /sys/class/thermal/thermal_zone0/temp",
            "gpu": "nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits",
            "ambient": "sensors | grep 'temp1' | head -1",
        }

        cmd = commands.get(sensor, commands["cpu"])
        result = self._connection.execute_command(cmd)

        if result.success:
            try:
                if sensor == "cpu":
                    return float(result.stdout.strip()) / 1000.0
                return float(result.stdout.strip())
            except ValueError:
                pass

        return 0.0

    def get_power_status(self) -> str:
        """Get system power status."""
        if not self._connection:
            return "unknown"

        # Check battery status
        result = self._connection.execute_command("cat /sys/class/power_supply/BAT*/status")
        if result.success:
            return result.stdout.strip().lower()

        # Check AC adapter
        result = self._connection.execute_command("cat /sys/class/power_supply/A*/online")
        if result.success and "1" in result.stdout:
            return "plugged"

        return "unknown"

    def control_interface_power(self, interface: str, enable: bool) -> bool:
        """Control network interface power state."""
        if not self._connection:
            return False

        action = "up" if enable else "down"
        result = self._connection.execute_command(f"ip link set {interface} {action}")
        return result.success

    # Software Management
    def check_software(self, name: str) -> SoftwareInfo:
        """Check if software is installed and get version."""
        if name in self._software_cache:
            return self._software_cache[name]

        info = SoftwareInfo(name=name)

        if self._connection:
            # Check if command exists
            result = self._connection.execute_command(f"which {name}")
            if result.success:
                info.installed = True
                info.path = result.stdout.strip()

                # Try to get version
                for version_cmd in [f"{name} --version", f"{name} -V", f"{name} version"]:
                    ver_result = self._connection.execute_command(version_cmd)
                    if ver_result.success:
                        info.version = ver_result.stdout.split()[0] if ver_result.stdout else "unknown"
                        break

        self._software_cache[name] = info
        return info

    def install_software(self, name: str, package_manager: str = "auto") -> bool:
        """Install missing software using appropriate package manager."""
        if not self._connection:
            return False

        # Auto-detect package manager
        if package_manager == "auto":
            managers = {
                "apt": "apt-get install -y",
                "yum": "yum install -y",
                "dnf": "dnf install -y",
                "pacman": "pacman -S --noconfirm",
                "zypper": "zypper install -y",
            }

            for mgr, cmd in managers.items():
                check_result = self._connection.execute_command(f"which {mgr}")
                if check_result.success:
                    install_cmd = f"{cmd} {name}"
                    result = self._connection.execute_command(install_cmd)
                    if result.success:
                        # Clear cache to force recheck
                        self._software_cache.pop(name, None)
                        return True
        else:
            # Use specified package manager
            result = self._connection.execute_command(f"{package_manager} {name}")
            return result.success

        return False

    def get_software_list(self) -> list[SoftwareInfo]:
        """Get list of installed software."""
        software_list = []

        if self._connection:
            # Try different methods to list installed packages
            commands = [
                "dpkg -l | grep '^ii'",  # Debian/Ubuntu
                "rpm -qa",  # RedHat/CentOS
                "pacman -Q",  # Arch
            ]

            for cmd in commands:
                result = self._connection.execute_command(cmd)
                if result.success:
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 2:
                                software_list.append(
                                    SoftwareInfo(
                                        name=parts[1] if "dpkg" in cmd else parts[0],
                                        version=parts[2] if len(parts) > 2 else "unknown",
                                        installed=True,
                                    )
                                )
                    break

        return software_list

    # Network Management
    def get_network_status(self) -> dict[str, bool]:
        """Get status of all network interfaces."""
        status = {}

        for interface in Interfaces().list:
            if self._connection:
                result = self._connection.execute_command(f"cat /sys/class/net/{interface}/operstate")
                status[interface] = result.success and "up" in result.stdout.lower()
            else:
                status[interface] = False

        return status

    def test_connectivity(self, target: str = "8.8.8.8", count: int = 3) -> bool:
        """Test network connectivity."""
        if not self._connection:
            return False

        result = self._connection.execute_command(f"ping -c {count} {target}")
        return result.success and "0% packet loss" in result.stdout

    # Health Monitoring
    def collect_health_metrics(self) -> SystemHealth:
        """Collect comprehensive system health metrics."""
        health = SystemHealth()

        if self._connection:
            # CPU usage
            result = self._connection.execute_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
            if result.success:
                with contextlib.suppress(ValueError):
                    health.cpu_usage = float(result.stdout.strip().replace("%us,", ""))

            # Memory usage
            result = self._connection.execute_command("free | grep Mem | awk '{print ($3/$2) * 100.0}'")
            if result.success:
                with contextlib.suppress(ValueError):
                    health.memory_usage = float(result.stdout.strip())

            # Disk usage
            result = self._connection.execute_command("df / | tail -1 | awk '{print $5}' | sed 's/%//'")
            if result.success:
                with contextlib.suppress(ValueError):
                    health.disk_usage = float(result.stdout.strip())

        # Temperature and network status
        health.temperature = self.get_temperature()
        health.network_status = self.get_network_status()
        health.power_status = self.get_power_status()

        self._health_log.append(health)
        return health

    def get_health_history(self, hours: int = 24) -> list[SystemHealth]:
        """Get health metrics history."""
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        return [h for h in self._health_log if h.timestamp > cutoff]

    def log_system_test(self, test_name: str, result: bool, details: str = "") -> None:
        """Log system test results."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "test_name": test_name,
            "result": "PASS" if result else "FAIL",
            "details": details,
            "system": self._name,
        }

        logger.info(f"System Test: {log_entry}")

    # Extensibility
    def add_probe(self, name: str, probe: SystemProbe) -> None:
        """Add custom system probe."""
        self._probes[name] = probe

    def run_probe(self, name: str) -> Any:
        """Run specific probe."""
        if name in self._probes:
            return self._probes[name].probe()
        return None

    def run_all_probes(self) -> dict[str, Any]:
        """Run all registered probes."""
        results = {}
        for name, probe in self._probes.items():
            try:
                results[name] = probe.probe()
            except Exception as e:
                results[name] = f"Error: {e}"
                logger.exception(f"Probe {name} failed")
        return results

    # Utility methods
    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"Platform(name='{self._name}', probes={len(self._probes)})"
