from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.platform.enums.software import PackageStatus


@dataclass(frozen=True)
class Service:
    """System service information."""

    name: str = ""
    status: str = "unknown"
    enabled: bool = False
    pid: int | None = None


@dataclass(frozen=True)
class Package:
    """Software package information."""

    def __init__(
        self,
        name: str = "",
        version: str = "",
        installed: PackageStatus = PackageStatus.UNKNOWN,
        path: str | None = None,
        size: float | None = None,
        description: str = "",
        execution_time: float = 0.0,
    ):
        """Initialize package.

        Args:
            name: Package name
            version: Package version
            installed: Installation status
            path: Installation path
            size: Package size
            description: Package description
            execution_time: Execution time
        """
        self.name = name
        self.version = version
        self.installed = installed
        self.path = path
        self.size = size
        self.description = description
        self.execution_time = execution_time


class IPackageManager(ABC):
    """Abstract interface for package managers."""

    @abstractmethod
    def install(self, package: str, sudo_pass: str) -> bool:
        """Install package.

        Args:
            package: Package name
            sudo_pass: Sudo password

        Returns:
            True if successful
        """

    @abstractmethod
    def remove(self, package: str) -> bool:
        """Remove package.

        Args:
            package: Package name

        Returns:
            True if successful
        """

    @abstractmethod
    def get_package_info(self, package: str) -> Package:
        """List installed packages.

        Args:
            package: Package name

        Returns:
            Package information
        """

    @abstractmethod
    def _parse_version(self, output: str) -> Package:
        """Parse package output text.

        Args:
            output: Command output

        Returns:
            Package information
        """

    @abstractmethod
    def is_available(self) -> bool:
        """Check if package manager is available.

        Returns:
            True if available
        """
