"""Software management module for SUT platforms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Package:
    """Software package information."""

    name: str = ""
    version: str = "unknown"
    installed: bool = False
    path: str | None = None
    size: int | None = None
    description: str = ""


@dataclass(frozen=True)
class Service:
    """System service information."""

    name: str = ""
    status: str = "unknown"
    enabled: bool = False
    pid: int | None = None


class PackageManager(ABC):
    """Abstract package manager interface."""

    @abstractmethod
    def install(self, package: str) -> bool:
        """Install package."""

    @abstractmethod
    def remove(self, package: str) -> bool:
        """Remove package."""

    @abstractmethod
    def list_installed(self) -> list[Package]:
        """List installed packages."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if package manager is available."""


class AptManager(PackageManager):
    """APT package manager for Debian/Ubuntu."""

    def __init__(self, connection):
        self._connection = connection

    def install(self, package: str) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command(f"apt-get install -y {package}")
        return result.success

    def remove(self, package: str) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command(f"apt-get remove -y {package}")
        return result.success

    def list_installed(self) -> list[Package]:
        if not self._connection:
            return []

        result = self._connection.execute_command("dpkg -l")
        if not result.success:
            return []

        packages = []
        for line in result.stdout.split("\n"):
            if line.startswith("ii"):
                parts = line.split()
                if len(parts) >= 3:
                    packages.append(
                        Package(
                            name=parts[1],
                            version=parts[2],
                            installed=True,
                            description=" ".join(parts[4:]) if len(parts) > 4 else "",
                        )
                    )
        return packages

    def is_available(self) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command("which apt-get")
        return result.success


class YumManager(PackageManager):
    """YUM package manager for RedHat/CentOS."""

    def __init__(self, connection):
        self._connection = connection

    def install(self, package: str) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command(f"yum install -y {package}")
        return result.success

    def remove(self, package: str) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command(f"yum remove -y {package}")
        return result.success

    def list_installed(self) -> list[Package]:
        if not self._connection:
            return []

        result = self._connection.execute_command("rpm -qa --queryformat '%{NAME} %{VERSION} %{SIZE}\\n'")
        if not result.success:
            return []

        packages = []
        for line in result.stdout.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                packages.append(
                    Package(
                        name=parts[0],
                        version=parts[1],
                        installed=True,
                        size=int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                    )
                )
        return packages

    def is_available(self) -> bool:
        if not self._connection:
            return False
        result = self._connection.execute_command("which yum")
        return result.success


class Software:
    """Independent software management class."""

    def __init__(self, connection=None):
        self._connection = connection
        self._managers: list[PackageManager] = []
        self._cache: dict[str, Package] = {}
        self._setup_managers()

    def _setup_managers(self):
        """Setup available package managers."""
        if not self._connection:
            return

        managers = [
            AptManager(self._connection),
            YumManager(self._connection),
        ]

        self._managers = [mgr for mgr in managers if mgr.is_available()]

    def check_software(self, name: str) -> Package:
        """Check if software is installed."""
        if name in self._cache:
            return self._cache[name]

        package = Package(name=name)

        if not self._connection:
            return package

        # Check if command exists
        result = self._connection.execute_command(f"which {name}")
        if result.success:
            package = Package(name=name, installed=True, path=result.stdout.strip())

            # Try to get version
            for version_cmd in [f"{name} --version", f"{name} -V", f"{name} version"]:
                ver_result = self._connection.execute_command(version_cmd)
                if ver_result.success:
                    version_line = ver_result.stdout.split("\n")[0]
                    version = self._extract_version(version_line)
                    package = Package(
                        name=package.name, version=version, installed=package.installed, path=package.path
                    )
                    break

        self._cache[name] = package
        return package

    def install_software(self, name: str) -> bool:
        """Install software using available package manager."""
        for manager in self._managers:
            if manager.install(name):
                # Clear cache to force recheck
                self._cache.pop(name, None)
                return True
        return False

    def remove_software(self, name: str) -> bool:
        """Remove software using available package manager."""
        for manager in self._managers:
            if manager.remove(name):
                # Clear cache to force recheck
                self._cache.pop(name, None)
                return True
        return False

    def get_installed_packages(self) -> list[Package]:
        """Get list of all installed packages."""
        all_packages = []
        for manager in self._managers:
            packages = manager.list_installed()
            all_packages.extend(packages)
        return all_packages

    def get_services(self) -> list[Service]:
        """Get system services information."""
        if not self._connection:
            return []

        services = []

        # Try systemctl first
        result = self._connection.execute_command("systemctl list-units --type=service --no-pager")
        if result.success:
            for line in result.stdout.split("\n")[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 4 and parts[0].endswith(".service"):
                    name = parts[0].replace(".service", "")
                    status = parts[2] if len(parts) > 2 else "unknown"
                    services.append(Service(name=name, status=status, enabled=status == "active"))

        return services

    def get_service_status(self, service_name: str) -> Service:
        """Get specific service status."""
        if not self._connection:
            return Service(name=service_name)

        result = self._connection.execute_command(f"systemctl status {service_name}")
        if not result.success:
            return Service(name=service_name)

        status = "inactive"
        enabled = False
        pid = None

        for line in result.stdout.split("\n"):
            if "Active:" in line:
                if "active (running)" in line:
                    status = "active"
                    enabled = True
            elif "Main PID:" in line:
                try:
                    pid_part = line.split("Main PID:")[1].split()[0]
                    pid = int(pid_part)
                except (ValueError, IndexError):
                    pass

        return Service(name=service_name, status=status, enabled=enabled, pid=pid)

    def start_service(self, service_name: str) -> bool:
        """Start a system service."""
        if not self._connection:
            return False
        result = self._connection.execute_command(f"systemctl start {service_name}")
        return result.success

    def stop_service(self, service_name: str) -> bool:
        """Stop a system service."""
        if not self._connection:
            return False
        result = self._connection.execute_command(f"systemctl stop {service_name}")
        return result.success

    def enable_service(self, service_name: str) -> bool:
        """Enable a system service."""
        if not self._connection:
            return False
        result = self._connection.execute_command(f"systemctl enable {service_name}")
        return result.success

    def disable_service(self, service_name: str) -> bool:
        """Disable a system service."""
        if not self._connection:
            return False
        result = self._connection.execute_command(f"systemctl disable {service_name}")
        return result.success

    def clear_cache(self) -> None:
        """Clear software cache."""
        self._cache.clear()

    def _extract_version(self, version_line: str) -> str:
        """Extract version from version output."""
        # Look for version patterns like 1.2.3, v1.2.3, version 1.2.3
        patterns = [
            r"v?(\d+\.\d+\.\d+)",
            r"version\s+(\d+\.\d+\.\d+)",
            r"(\d+\.\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, version_line, re.IGNORECASE)
            if match:
                return match.group(1)

        return "unknown"
