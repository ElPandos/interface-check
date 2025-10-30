"""Software management module for SUT platforms.

This module provides comprehensive software package management capabilities
for remote systems via SSH connections. It automatically detects the available
package manager (APT or YUM) and provides a unified interface for package
operations including installation, removal, and version checking.

Key Features:
- Auto-detection of package manager (APT/YUM)
- Unified interface for package operations
- Version extraction and validation
- Service management capabilities
- Comprehensive logging and error handling

Supported Package Managers:
- APT (Debian/Ubuntu systems)
- YUM (RedHat/CentOS systems)
"""

import logging
import re
from typing import ClassVar

from src.core.connect import SshConnection
from src.interfaces.connection import CommandResult
from src.interfaces.software import IPackageManager, Package
from src.platform.enums.log import LogName
from src.platform.enums.software import PackageManagerType

# fmt: off
SUPPORTED_PACKAGES: list[str] = {
    "pciutils",         # PCI utilities for hardware info
    "ethtool",          # Ethernet tool for NIC management
    "rdma-core",        # RDMA/InfiniBand tools
    "ibverbs-utils",    # RDMA/InfiniBand tools
    "lshw",             # Hardware lister
    "lm-sensors",       # Hardware monitoring sensors
    "python3-pip",      # Python package installer
    "mstflint",         # Mellanox firmware tools
    "mlnx-tools",       # Mellanox configuration tools
}
# fmt: on


class AptManager(IPackageManager):
    """APT package manager implementation for Debian/Ubuntu systems.

    This class provides APT-specific package management operations including
    installation, removal, and package listing. It uses dpkg and apt-get
    commands to interact with the package system.

    Attributes:
        _ssh_connection: SSH connection for executing remote commands
        logger: Logger instance for operation tracking
    """

    def __init__(self, ssh_connection: SshConnection):
        """Initialize APT manager with SSH connection.

        Args:
            ssh_connection: Active SSH connection to target system
        """
        super().__init__()
        self._ssh_connection = ssh_connection

        self.logger = logging.getLogger(LogName.MAIN.value)
        self.logger.debug("Initialized APT package manager")

    def install(self, package: str, sudo_pass: str) -> bool:
        """Install a package using apt-get.

        Args:
            package: Name of package to install
            sudo_pass: Sudo password for authentication

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package installation")
            return False

        self.logger.info(f"Installing package '{package}' using APT")

        # Use echo to pipe password to sudo for non-interactive installation
        cmd = f"echo '{sudo_pass}' | sudo -S apt-get install -y {package}"
        result = self._ssh_connection.execute_command(cmd)

        if result.success:
            self.logger.info(f"Successfully installed package '{package}'")
        else:
            self.logger.error(f"Failed to install package '{package}': {result.stderr}")

        return result.success

    def remove(self, package: str = "") -> bool:
        """Remove a package using apt-get.

        Args:
            package: Name of package to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package removal")
            return False

        if not package:
            self.logger.warning("No package name provided for removal")
            return False

        self.logger.info(f"Removing package '{package}' using APT")

        # Execute apt-get remove with -y flag for non-interactive removal
        result = self._ssh_connection.execute_command(f"apt-get remove -y {package}")
        success = hasattr(result, "success") and result.success

        if success:
            self.logger.info(f"Successfully removed package '{package}'")
        else:
            self.logger.error(f"Failed to remove package '{package}'")

        return success

    def get_package_info(self, package: str) -> Package | None:
        """List all installed packages using dpkg.

        Returns:
            list[Package]: List of installed packages with metadata
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package listing")
            return None

        self.logger.debug("Retrieving list of installed packages using dpkg")

        # Use dpkg -l to list all installed packages
        result = self._ssh_connection.execute_command(f"dpkg -l {package}")
        if result.success:
            return self._parse_version(result.stdout)

        self.logger.error("Failed to retrieve package list from dpkg")
        return None

    def _parse_version(self, output: str) -> list[Package]:
        """Parse dpkg -l output into Package object.

        Args:
            output: Raw output from dpkg -l command

        Returns:
            list[Package]: Parsed package information
        """
        output = output.encode().decode("unicode_escape")  # turns "\n" into real newlines
        match = re.search(r"^[a-z]{2}\s+\S+\s+(\S+)", output, re.MULTILINE)
        version = ""
        if match:
            version = match.group(1)
            self.logger.debug(f"Successfully parsed version: {version}")
        else:
            self.logger.error("Failed to parse verssion")

        return version

    def is_available(self) -> bool:
        """Check if APT package manager is available on the system.

        Returns:
            bool: True if apt-get command is available, False otherwise
        """
        if not self._ssh_connection:
            self.logger.debug("No SSH connection available for APT availability check")
            return False

        self.logger.debug("Checking APT availability using 'which apt-get'")

        # Check if apt-get command exists in PATH
        result = self._ssh_connection.execute_command("which apt-get")

        if result.success:
            self.logger.info("APT package manager is available")
        else:
            self.logger.debug("APT package manager is not available")

        return result.success


class YumManager(IPackageManager):
    """YUM package manager implementation for RedHat/CentOS systems.

    This class provides YUM-specific package management operations including
    installation, removal, and package listing. It uses yum and rpm commands
    to interact with the package system.

    Attributes:
        _ssh_connection: SSH connection for executing remote commands
        logger: Logger instance for operation tracking
    """

    def __init__(self, ssh_connection: SshConnection):
        """Initialize YUM manager with SSH connection.

        Args:
            ssh_connection: Active SSH connection to target system
        """
        self._ssh_connection = ssh_connection
        self.logger = logging.getLogger(LogName.MAIN.value)
        self.logger.debug("Initialized YUM package manager")

    def install(self, package: str, sudo_pass: str) -> bool:
        """Install a package using yum.

        Args:
            package: Name of package to install
            sudo_pass: Sudo password for authentication

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package installation")
            return False

        self.logger.info(f"Installing package '{package}' using YUM")

        # Use echo to pipe password to sudo for non-interactive installation
        cmd = f"echo '{sudo_pass}' | sudo -S yum install -y {package}"
        result = self._ssh_connection.execute_command(cmd)
        if result.success:
            self.logger.info(f"Successfully installed package '{package}'")
        else:
            self.logger.error(f"Failed to install package '{package}': {result.stderr}")

        return result.success

    def remove(self, package: str) -> bool:
        """Remove a package using yum.

        Args:
            package: Name of package to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package removal")
            return False

        if not package:
            self.logger.warning("No package name provided for removal")
            return False

        self.logger.info(f"Removing package '{package}' using YUM")

        # Execute yum remove with -y flag for non-interactive removal
        result = self._ssh_connection.execute_command(f"yum remove -y {package}")
        success = hasattr(result, "success") and result.success

        if success:
            self.logger.info(f"Successfully removed package '{package}'")
        else:
            self.logger.error(f"Failed to remove package '{package}'")

        return success

    def get_package_info(self, package: str) -> Package:
        """List all installed packages using rpm.


        Returns:
            list[Package]: List of installed packages with metadata
        """
        self.logger.error("Not implemented yet")
        return None

        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package listing")
            return []

        self.logger.debug("Retrieving list of installed packages using rpm")

        # Use rpm -qa with custom format to get package info
        # Format: NAME VERSION SIZE (one per line)
        result = self._ssh_connection.execute_command(
            "rpm -qa --queryformat '%{NAME} %{VERSION} %{SIZE}\\n'"
        )
        if not (hasattr(result, "success") and result.success):
            self.logger.error("Failed to retrieve package list from rpm")
            return []

        packages = self._parse_version(result.stdout)
        self.logger.info(f"Found {len(packages)} installed packages")
        return packages

    def _parse_version(self, output: str) -> str:
        """Parse rpm -qa output into Package objects.

        Args:
            output: Raw output from rpm -qa command

        Returns:
            list[Package]: Parsed package information
        """
        packages = []
        self.logger.error("NNot implemented yet")
        return None

        # Parse each line of rpm output
        # Format: package_name version size
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                # Extract size if available and numeric
                size = None
                if len(parts) > 2 and parts[2].isdigit():
                    size = int(parts[2])

                package = Package(
                    name=parts[0],  # Package name
                    version=parts[1],  # Version string
                    installed=True,  # Mark as installed
                    size=size,  # Package size in bytes (if available)
                )
                packages.append(package)
                self.logger.debug(f"Parsed package: {parts[0]} v{parts[1]}")

        return packages

    def is_available(self) -> bool:
        """Check if YUM package manager is available on the system.

        Returns:
            bool: True if yum command is available, False otherwise
        """
        if not self._ssh_connection:
            self.logger.debug("No SSH connection available for YUM availability check")
            return False

        self.logger.debug("Checking YUM availability using 'which yum'")

        # Check if yum command exists in PATH
        result = self._ssh_connection.execute_command("which yum")
        if result.success:
            self.logger.info("YUM package manager is available")
        else:
            self.logger.debug("YUM package manager is not available")

        return result.success


class SoftwareManager:
    """Unified software management interface with automatic package manager detection.

    This class provides a high-level interface for software management operations
    that automatically detects the available package manager (APT or YUM) and
    delegates operations to the appropriate implementation.

    Features:
    - Automatic package manager detection
    - Unified interface for different package managers
    - Software version extraction and validation
    - Package installation caching
    - Service management capabilities
    - Comprehensive logging and error handling

    Attributes:
        VERSION_PATTERNS: Regex patterns for version extraction
        _ssh_connection: SSH connection for remote operations
        _cache: Cache for package information
        _package_manager: Detected package manager instance
        logger: Logger instance for operation tracking
    """

    # Regular expression patterns for extracting version numbers from command output
    # These patterns match common version formats like "1.2.3", "v1.2.3", "version 1.2.3"
    VERSION_PATTERNS: ClassVar[list[str]] = [
        r"v?(\d+\.\d+\.\d+)",  # Matches v1.2.3 or 1.2.3 (semantic versioning)
        r"version\s+(\d+\.\d+\.\d+)",  # Matches "version 1.2.3"
        r"(\d+\.\d+)",  # Matches 1.2 (major.minor)
    ]

    def __init__(self, ssh_connection: SshConnection):
        """Initialize software manager with SSH connection and detect package manager.

        Args:
            ssh_connection: Active SSH connection to target system
        """
        self._ssh_connection = ssh_connection
        self._cache: dict[str, Package] = {}  # Cache for package information
        self._package_manager: IPackageManager | None = None

        # Initialize logger first for detection logging
        self.logger = logging.getLogger(LogName.MAIN.value)
        self.logger.info("Initializing Software Manager")

        # Other logger
        self.sut_system_info_logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)

        # Detect and initialize the appropriate package manager
        self._detect_package_manager()

    def _detect_package_manager(self) -> None:
        """Detect and initialize the appropriate package manager.

        This method attempts to detect which package manager is available
        on the target system by checking for APT first, then YUM.
        The first available package manager is selected and initialized.
        """
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for package manager detection")
            return

        self.logger.info("Detecting available package manager")

        try:
            # Try APT first (Debian/Ubuntu systems)
            self.logger.debug("Checking for APT package manager")
            apt_manager = AptManager(self._ssh_connection)
            if apt_manager.is_available():
                self._package_manager = apt_manager
                self.logger.info("Detected APT package manager (Debian/Ubuntu system)")
                return
        except Exception as e:
            self.logger.warning(f"Error checking APT availability: {e}")

        try:
            # Try YUM (RedHat/CentOS systems)
            self.logger.debug("Checking for YUM package manager")
            yum_manager = YumManager(self._ssh_connection)
            if yum_manager.is_available():
                self._package_manager = yum_manager
                self.logger.info("Detected YUM package manager (RedHat/CentOS system)")
                return
        except Exception as e:
            self.logger.warning(f"Error checking YUM availability: {e}")

        # No package manager detected
        self.logger.warning("No supported package manager detected (APT/YUM)")

    def _is_connected(self) -> bool:
        """Check if SSH connection is available.

        Returns:
            bool: True if SSH connection exists, False otherwise
        """
        if not self._ssh_connection:
            self.logger.debug("SSH connection is not available")
            return False
        return True

    def _execute_command(self, command: str) -> CommandResult:
        """Execute command safely with error handling and logging.

        Args:
            command: Command to execute on remote system

        Returns:
            tuple[bool, str]: (success_status, command_output)
        """
        if not self._is_connected():
            self.logger.error(f"Cannot execute command '{command}': No SSH connection")
            return False, ""

        try:
            self.logger.debug(f"Executing command: {command}")
            result = self._ssh_connection.execute_command(command)
            if result.success:
                self.logger.debug(f"Command executed successfully: {command}")
            else:
                self.logger.warning(f"Command failed: {command}")

            return result.success, result.stdout.strip()
        except Exception:
            self.logger.exception(f"Exception executing command: {command}")
            return False, ""

    def get_package_manager_type(self) -> PackageManagerType:
        """Get the type of package manager being used.

        Returns:
            PackageManagerType: The detected package manager type
        """
        if isinstance(self._package_manager, AptManager):
            self.logger.debug("Package manager type: APT")
            return PackageManagerType.APT
        if isinstance(self._package_manager, YumManager):
            self.logger.debug("Package manager type: YUM")
            return PackageManagerType.YUM

        self.logger.debug("Package manager type: UNKNOWN")
        return PackageManagerType.UNKNOWN

    def _validate_package_support(
        self, required_packages: list[str]
    ) -> tuple[list[str], list[str]]:
        """Validate package support and separate into supported/unsupported lists.

        Args:
            required_packages: List of package names to validate

        Returns:
            tuple: (supported_packages, unsupported_packages)
        """
        supported = [pkg for pkg in required_packages if pkg in SUPPORTED_PACKAGES]
        unsupported = [pkg for pkg in required_packages if pkg not in SUPPORTED_PACKAGES]

        if unsupported:
            self.logger.warning(
                f"Unsupported packages (no version check available): {', '.join(unsupported)}"
            )

        return supported, unsupported

    def install_required_packages(self, required_packages: list[str], sudo_pass: str) -> bool:
        """Install all required software packages using detected package manager.

        This method installs packages one by one for better error handling
        and logging. It provides detailed feedback on each installation attempt.

        Args:
            required_packages: List of package names to install
            sudo_pass: Sudo password for authentication

        Returns:
            bool: True if all packages installed successfully, False otherwise
        """
        if not required_packages:
            self.logger.info("No packages specified for installation")
            return True

        if not self._package_manager:
            self.logger.error("Cannot install packages: No package manager available")
            return False

        # Validate package support
        supported_packages, _ = self._validate_package_support(required_packages)

        self.logger.info(
            f"Installing {len(supported_packages)} required packages: {', '.join(supported_packages)}"
        )

        # Install packages one by one for better error handling and logging
        success_count = 0
        failed_packages = []

        for package in supported_packages:
            self.logger.info(
                f"Installing package {success_count + 1}/{len(supported_packages)}: {package}"
            )

            if self._package_manager.install(package, sudo_pass):
                success_count += 1
                self.logger.info(f"Successfully installed: {package}")
            else:
                failed_packages.append(package)
                self.logger.error(f"Failed to install: {package}")

        # Log installation summary
        if success_count == len(supported_packages):
            self.logger.info(f"All {len(supported_packages)} packages installed successfully")
        else:
            self.logger.warning(
                f"Installed {success_count}/{len(supported_packages)} packages. "
                f"Failed: {', '.join(failed_packages)}"
            )

        return success_count == len(supported_packages)

    def log_required_package_versions(self, required_packages: list[str] | None = None) -> None:
        """Log installed required packages versions.

        This method checks the versions of commonly used network tools
        and utilities to verify they are properly installed.

        Args:
            required_packages: Optional list of specific packages to check.
                             If None, checks all SUPPORTED_COMMANDS.
        """
        self.logger.info("Verifying installed package versions")

        # If no specific list provided, use all supported commands
        if required_packages is None:
            packages_to_check = list(SUPPORTED_PACKAGES.keys())
        else:
            # Validate package support
            packages_to_check, _ = self._validate_package_support(required_packages)

        version_info = {}
        # Check each supported command for version information
        for pkg in packages_to_check:
            self.logger.debug(f"Checking version for package: {pkg}")
            if pkg in SUPPORTED_PACKAGES:
                version_info[pkg] = self._package_manager.get_package_info(pkg)
            else:
                version_info[pkg] = "Unsupported package"

        self._log_installation(version_info)

    def _log_installation(self, version_info: dict[str, str]) -> None:
        """Display software versions in a pretty table format.

        Args:
            version_info: Dictionary mapping package names to version strings
        """
        self.logger.info(f"Version verification complete for {len(version_info)} packages")

        table_config = self._calculate_table_dimensions(version_info)
        installed_packages, missing_packages = self._separate_packages_by_status(version_info)

        self._log_table_header(table_config)
        self._log_package_rows(installed_packages, missing_packages, table_config)
        self._log_table_footer(table_config)
        self._log_summary_statistics(version_info)

    def _calculate_table_dimensions(self, version_info: dict[str, str]) -> dict[str, int]:
        """Calculate table column widths and formatting dimensions.

        Args:
            version_info: Package version information

        Returns:
            dict: Table configuration with widths and formatting strings
        """
        max_name_width = max(len(pkg) for pkg in version_info) + 2
        max_version_width = max(len(version) for version in version_info.values()) + 2

        name_width = max(max_name_width, 20)
        version_width = max(max_version_width, 30)
        status_width = 10
        table_width = name_width + version_width + status_width + 7

        return {
            "name_width": name_width,
            "version_width": version_width,
            "status_width": status_width,
            "table_width": table_width,
            "header_line": "═" * table_width,
            "separator_line": "─" * table_width,
        }

    def _separate_packages_by_status(
        self, version_info: dict[str, str]
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        """Separate packages into installed and missing categories.

        Args:
            version_info: Package version information

        Returns:
            tuple: (installed_packages, missing_packages)
        """
        installed_packages = []
        missing_packages = []

        for pkg, version in sorted(version_info.items()):
            if "Not found" in version or "error" in version.lower():
                missing_packages.append((pkg, version))
            else:
                installed_packages.append((pkg, version))

        return installed_packages, missing_packages

    def _log_table_header(self, config: dict[str, int]) -> None:
        """Log formatted table header.

        Args:
            config: Table configuration dictionary
        """
        self.sut_system_info_logger.info(f"{config['header_line']}")
        self.sut_system_info_logger.info(
            f"| {'Package':<{config['name_width'] - 2}} | {'Version Information':<{config['version_width'] - 2}} | {'Status':<{config['status_width'] - 2}} |"
        )
        self.sut_system_info_logger.info(f"{config['header_line']}")

    def _log_package_rows(
        self,
        installed: list[tuple[str, str]],
        missing: list[tuple[str, str]],
        config: dict[str, int],
    ) -> None:
        """Log package rows with status formatting.

        Args:
            installed: List of installed packages
            missing: List of missing packages
            config: Table configuration dictionary
        """
        # Log installed packages
        for pkg, version in installed:
            self._log_package_row(pkg, version, "INSTALLED", "", config)

        # Add separator if both categories exist
        if installed and missing:
            self.logger.info(f"{config['separator_line']}")

        # Log missing packages
        for pkg, version in missing:
            self._log_package_row(pkg, version, "MISSING", "", config)

    def _log_package_row(
        self, pkg: str, version: str, status: str, color: str, config: dict[str, int]
    ) -> None:
        """Log a single package row with formatting.

        Args:
            pkg: Package name
            version: Package version
            status: Package status (INSTALLED/MISSING)
            color: ANSI color code (unused for plain text)
            config: Table configuration dictionary
        """
        display_version = (
            version[: config["version_width"] - 4] + "..."
            if len(version) > config["version_width"] - 2
            else version
        )

        self.sut_system_info_logger.info(
            f"| {pkg:<{config['name_width'] - 2}} | {display_version:<{config['version_width'] - 2}} | {status:<{config['status_width'] - 2}} |"
        )
        self.logger.debug(f"Package '{pkg}' status: {status}")

    def _log_table_footer(self, config: dict[str, int]) -> None:
        """Log table footer.

        Args:
            config: Table configuration dictionary
        """
        self.sut_system_info_logger.info(f"{config['header_line']}")

    def _log_summary_statistics(self, version_info: dict[str, str]) -> None:
        """Log installation summary statistics.

        Args:
            version_info: Package version information
        """
        total_packages = len(version_info)
        successful = sum(
            1 for v in version_info.values() if "Not found" not in v and "error" not in v.lower()
        )
        failed = total_packages - successful
        success_rate = (successful / total_packages * 100) if total_packages > 0 else 0

        self.sut_system_info_logger.info("Software Installation Verification Summary")
        self.sut_system_info_logger.info(f"   Total packages verified: {total_packages}")
        self.sut_system_info_logger.info(
            f"   Successfully installed: {successful} ({success_rate:.1f}%)"
        )
        if failed > 0:
            self.sut_system_info_logger.info(
                f"   Missing or failed: {failed} ({100 - success_rate:.1f}%)"
            )
            self.sut_system_info_logger.warning(
                "Some required packages are missing. Consider installing them manually."
            )
        else:
            self.sut_system_info_logger.info("   All required packages are properly installed!")
        self.sut_system_info_logger.info("")

    # def log_system_info(self, required_packages: list[Package]) -> None:
    #     if not self._package_manager:
    #         self.logger.error("Cannot update package index: No package manager available")
    #         return

    #     # Validate package support
    #     supported_packages, _ = self._validate_package_support(required_packages)

    #     for package in supported_packages:
    #         self.log_system_info()

    def update_installed_packages(self) -> bool:
        """Update package index using detected package manager.

        Returns:
            bool: True if update successful, False otherwise
        """
        if not self._package_manager:
            self.logger.error("Cannot update package index: No package manager available")
            return False

        self.logger.info("Updating package index")

        # Use appropriate update command based on package manager type
        if isinstance(self._package_manager, AptManager):
            self.logger.debug("Updating APT package index")
            success, _ = self._execute_command("sudo apt update -y")
        elif isinstance(self._package_manager, YumManager):
            self.logger.debug("Updating YUM package cache")
            success, _ = self._execute_command("sudo yum check-update")
        else:
            self.logger.error("Unknown package manager type for index update")
            return False

        if success:
            self.logger.info("Package index updated successfully")
        else:
            self.logger.error("Failed to update package index")

        # await self.log_required_pakages_versions()

        return success
