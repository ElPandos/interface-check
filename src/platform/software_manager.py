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

from src.core.cli import PrettyFrame
from src.core.connect import SshConnection
from src.core.enums.messages import LogMsg
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
        ssh: SSH connection for executing remote commands
        logger: Logger instance for operation tracking
    """

    def __init__(self, ssh: SshConnection):
        """Initialize APT manager with SSH connection.

        Args:
            ssh: Active SSH connection to target system
        """
        IPackageManager.__init__(self)

        self._ssh = ssh

        self._logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)
        self._logger.debug(LogMsg.SW_MGR_APT_INIT.value)

    def install(self, package: str) -> bool:
        """Install a package using apt-get.

        Args:
            package: Name of package to install

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return False

        self._logger.info(f"{LogMsg.SW_PKG_INSTALL.value} '{package}' using APT")

        # Use echo to pipe password to sudo for non-interactive installation
        result = self._ssh.exec_cmd(f"apt install -y {package}")

        if result.success:
            self._logger.info(f"{LogMsg.SW_PKG_INSTALL_SUCCESS.value}: {package}")
        else:
            self._logger.error(f"{LogMsg.SW_PKG_INSTALL_FAIL.value}: {package} - {result.stderr}")

        return result.success

    def remove(self, package: str = "") -> bool:
        """Remove a package using apt-get.

        Args:
            package: Name of package to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return False

        if not package:
            self._logger.warning("No package name provided for removal")
            return False

        self._logger.info(f"{LogMsg.SW_PKG_REMOVE.value} '{package}' using APT")

        # Execute apt-get remove with -y flag for non-interactive removal
        result = self._ssh.exec_cmd(f"apt-get remove -y {package}")

        if result.success:
            self._logger.info(f"{LogMsg.SW_PKG_REMOVE_SUCCESS.value}: {package}")
        else:
            self._logger.error(f"{LogMsg.SW_PKG_REMOVE_FAIL.value}: {package}")

        return result.success

    def get_package_info(self, package: str) -> Package | None:
        """Get package information using dpkg.

        Args:
            package: Name of package to query

        Returns:
            Package: Package information or None if not found
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return None

        self._logger.debug(LogMsg.SW_PKG_LIST.value)

        # Use dpkg -l to list all installed packages
        result = self._ssh.exec_cmd(f"dpkg -l {package}")

        if result.success:
            return self._parse_version(result.stdout)

        self._logger.error(LogMsg.SW_PKG_LIST_FAIL.value)
        return None

    def _parse_version(self, output: str) -> str:
        """Parse dpkg -l output to extract version string.

        Args:
            output: Raw output from dpkg -l command

        Returns:
            str: Extracted version string or empty string if not found
        """
        output = output.encode().decode("unicode_escape")  # turns "\n" into real newlines
        match = re.search(r"^[a-z]{2}\s+\S+\s+(\S+)", output, re.MULTILINE)
        version = ""
        if match:
            version = match.group(1)
            self._logger.debug(f"{LogMsg.SW_PKG_VERSION_PARSE.value}: {version}")
        else:
            self._logger.error(LogMsg.SW_PKG_VERSION_PARSE_FAIL.value)

        return version

    def is_available(self) -> bool:
        """Check if APT package manager is available on the system.

        Returns:
            bool: True if apt-get command is available, False otherwise
        """
        if not self._ssh:
            self._logger.debug(LogMsg.SSH_NO_CONN.value)
            return False

        self._logger.debug(LogMsg.SW_MGR_APT_CHECK.value)

        # Check if apt-get command exists in PATH
        result = self._ssh.exec_cmd("which apt-get")

        if result.success:
            self._logger.info(LogMsg.SW_MGR_APT_FOUND.value)
        else:
            self._logger.debug(LogMsg.SW_MGR_APT_NOT_FOUND.value)

        return result.success


class YumManager(IPackageManager):
    """YUM package manager implementation for RedHat/CentOS systems.

    This class provides YUM-specific package management operations including
    installation, removal, and package listing. It uses yum and rpm commands
    to interact with the package system.

    Attributes:
        ssh: SSH connection for executing remote commands
        logger: Logger instance for operation tracking
    """

    def __init__(self, ssh: SshConnection):
        """Initialize YUM manager with SSH connection.

        Args:
            ssh: Active SSH connection to target system
        """
        IPackageManager.__init__(self)

        self._ssh = ssh

        self._logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)
        self._logger.debug(LogMsg.SW_MGR_YUM_INIT.value)

    def install(self, package: str) -> bool:
        """Install a package using yum.

        Args:
            package: Name of package to install

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return False

        self._logger.info(f"{LogMsg.SW_PKG_INSTALL.value} '{package}' using YUM")

        # Use echo to pipe password to sudo for non-interactive installation
        result = self._ssh.exec_cmd(f"yum install -y {package}")

        if result.success:
            self._logger.info(f"{LogMsg.SW_PKG_INSTALL_SUCCESS.value}: {package}")
        else:
            self._logger.error(f"{LogMsg.SW_PKG_INSTALL_FAIL.value}: {package} - {result.stderr}")

        return result.success

    def remove(self, package: str) -> bool:
        """Remove a package using yum.

        Args:
            package: Name of package to remove

        Returns:
            bool: True if removal successful, False otherwise
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return False

        if not package:
            self._logger.warning("No package name provided for removal")
            return False

        self._logger.info(f"{LogMsg.SW_PKG_REMOVE.value} '{package}' using YUM")

        # Execute yum remove with -y flag for non-interactive removal
        result = self._ssh.exec_cmd(f"yum remove -y {package}")

        if result.success:
            self._logger.info(f"{LogMsg.SW_PKG_REMOVE_SUCCESS.value}: {package}")
        else:
            self._logger.error(f"{LogMsg.SW_PKG_REMOVE_FAIL.value}: {package}")

        return result.success

    def get_package_info(self, package: str) -> Package | None:
        """Get package information using rpm.

        Args:
            package: Name of package to query

        Returns:
            Package: Package information or None if not implemented
        """
        self._logger.error("Not implemented yet")
        return None

        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return []

        self._logger.debug("Retrieving list of installed packages using rpm")

        # Use rpm -qa with custom format to get package info
        # Format: NAME VERSION SIZE (one per line)
        result = self._ssh.exec_cmd("rpm -qa --queryformat '%{NAME} %{VERSION} %{SIZE}\\n'")
        if not (hasattr(result, "success") and result.success):
            self._logger.error("Failed to retrieve package list from rpm")
            return []

        packages = self._parse_version(result.str_out)
        self._logger.info(f"Found {len(packages)} installed packages")
        return packages

    def _parse_version(self, output: str) -> str | None:
        """Parse rpm -qa output to extract version string.

        Args:
            output: Raw output from rpm -qa command

        Returns:
            str: Extracted version string or None if not implemented
        """
        packages = []
        self._logger.error("Not implemented yet")
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
                self._logger.debug(f"Parsed package: {parts[0]} v{parts[1]}")

        return packages

    def is_available(self) -> bool:
        """Check if YUM package manager is available on the system.

        Returns:
            bool: True if yum command is available, False otherwise
        """
        if not self._ssh:
            self._logger.debug(LogMsg.SSH_NO_CONN.value)
            return False

        self._logger.debug(LogMsg.SW_MGR_YUM_CHECK.value)

        # Check if yum command exists in PATH
        result = self._ssh.exec_cmd("which yum")

        if result.success:
            self._logger.info(LogMsg.SW_MGR_YUM_FOUND.value)
        else:
            self._logger.debug(LogMsg.SW_MGR_YUM_NOT_FOUND.value)

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
        ssh: SSH connection for remote operations
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

    def __init__(self, ssh: SshConnection):
        """Initialize software manager with SSH connection and detect package manager.

        Args:
            ssh: Active SSH connection to target system
        """
        self._ssh = ssh
        self._cache: dict[str, Package] = {}  # Cache for package information
        self._package_manager: IPackageManager | None = None

        # Initialize logger first for detection logging
        self._logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)
        self._logger.info(LogMsg.SW_MGR_INIT.value)

        # Detect and initialize the appropriate package manager
        self._detect_package_manager()

    def _detect_package_manager(self) -> None:
        """Detect and initialize the appropriate package manager.

        This method attempts to detect which package manager is available
        on the target system by checking for APT first, then YUM.
        The first available package manager is selected and initialized.
        """
        if not self._ssh:
            self._logger.error(LogMsg.SW_MGR_NO_SSH.value)
            return

        self._logger.info(LogMsg.SW_MGR_DETECT.value)

        try:
            # Try APT first (Debian/Ubuntu systems)
            self._logger.debug(LogMsg.SW_MGR_APT_CHECK.value)
            apt_manager = AptManager(self._ssh)
            if apt_manager.is_available():
                self._package_manager = apt_manager
                return
        except Exception as e:
            self._logger.warning(f"Error checking APT availability: {e}")

        try:
            # Try YUM (RedHat/CentOS systems)
            self._logger.debug(LogMsg.SW_MGR_YUM_CHECK.value)
            yum_manager = YumManager(self._ssh)
            if yum_manager.is_available():
                self._package_manager = yum_manager
                self._logger.info(LogMsg.SW_MGR_YUM_FOUND.value)
                return
        except Exception as e:
            self._logger.warning(f"Error checking YUM availability: {e}")

        # No package manager detected
        self._logger.warning(LogMsg.SW_MGR_NO_MANAGER.value)

    def _is_connected(self) -> bool:
        """Check if SSH connection is available.

        Returns:
            bool: True if SSH connection exists, False otherwise
        """
        if not self._ssh:
            self._logger.debug(LogMsg.SSH_NO_CONN.value)
            return False
        return True

    def _exec_cmd(self, cmd: str) -> tuple[bool, str]:
        """Execute command safely with error handling and logging.

        Args:
            cmd: Command to execute on remote system

        Returns:
            tuple[bool, str]: (success_status, command_output)
        """
        if not self._is_connected():
            self._logger.error(f"Cannot execute command '{cmd}': No SSH connection")
            return False, ""

        try:
            self._logger.debug(f"Executing command: '{cmd}'")
            result = self._ssh.exec_cmd(cmd)
            if result.success:
                self._logger.debug(f"Command executed successfully: {cmd}")
            else:
                self._logger.warning(f"Command failed: '{cmd}'")

            return result.success, result.stdout
        except Exception:
            self._logger.exception(f"Exception executing command: '{cmd}'")
            return False, ""

    def get_package_manager_type(self) -> PackageManagerType:
        """Get the type of package manager being used.

        Returns:
            PackageManagerType: The detected package manager type
        """
        if isinstance(self._package_manager, AptManager):
            self._logger.debug("Package manager type: APT")
            return PackageManagerType.APT
        if isinstance(self._package_manager, YumManager):
            self._logger.debug("Package manager type: YUM")
            return PackageManagerType.YUM

        self._logger.debug("Package manager type: UNKNOWN")
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
            self._logger.warning(f"{LogMsg.SW_PKG_VALIDATE.value}: {', '.join(unsupported)}")

        return supported, unsupported

    def install_required_packages(self, required_packages: list[str]) -> bool:
        """Install all required software packages using detected package manager.

        This method installs packages one by one for better error handling
        and logging. It provides detailed feedback on each installation attempt.

        Args:
            required_packages: List of package names to install

        Returns:
            bool: True if all packages installed successfully, False otherwise
        """
        if not required_packages:
            self._logger.info(LogMsg.SW_PKG_NO_PACKAGES.value)
            return True

        if not self._package_manager:
            self._logger.error(LogMsg.SW_PKG_NO_MANAGER.value)
            return False

        # Validate package support
        supported_packages, _ = self._validate_package_support(required_packages)

        self._logger.info(
            f"Installing {len(supported_packages)} required packages: {', '.join(supported_packages)}"
        )

        # Install packages one by one for better error handling and logging
        success_count = 0
        failed_packages = []

        for package in supported_packages:
            self._logger.info(
                f"Installing package ({success_count + 1}/{len(supported_packages)}) -> {package}"
            )

            if self._package_manager.install(package):
                success_count += 1
                self._logger.info(f"Successfully installed: {package}")
            else:
                failed_packages.append(package)
                self._logger.error(f"Failed to install: {package}")

        # Log installation summary
        if success_count == len(supported_packages):
            self._logger.info(f"{LogMsg.SW_PKG_INSTALL_SUMMARY.value} ({len(supported_packages)})")
        else:
            self._logger.warning(
                f"{LogMsg.SW_PKG_INSTALL_PARTIAL.value}: {success_count}/{len(supported_packages)}. "
                f"Failed: {', '.join(failed_packages)}"
            )

        return success_count == len(supported_packages)

    def log_required_package_versions(self, required_packages: list[str] | None = None) -> None:
        """Log installed required packages versions.

        This method checks the versions of commonly used network tools
        and utilities to verify they are properly installed.

        Args:
            required_packages: Optional list of specific packages to check.
                             If None, checks all SUPPORTED_PACKAGES.
        """
        self._logger.info(LogMsg.SW_PKG_VERSION_CHECK.value)

        # If no specific list provided, use all supported commands
        if required_packages is None:
            packages_to_check = list(SUPPORTED_PACKAGES.keys())
        else:
            # Validate package support
            packages_to_check, _ = self._validate_package_support(required_packages)

        version_info = {}
        # Check each supported command for version information
        for pkg in packages_to_check:
            self._logger.debug(f"Checking version for package: {pkg}")
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
        self._logger.info(
            f"{LogMsg.SW_PKG_VERSION_COMPLETE.value} for {len(version_info)} packages"
        )

        frame = PrettyFrame(width=80)
        rows = []

        # Separate packages by status
        installed_packages, missing_packages = self._separate_packages_by_status(version_info)

        # Add installed packages
        for pkg, version in installed_packages:
            rows.append(f"{pkg}: {version}")
            rows.append("  Status: INSTALLED")

        # Add missing packages
        for pkg, version in missing_packages:
            rows.append(f"{pkg}: {version}")
            rows.append("  Status: MISSING")

        # Log the framed table
        self._logger.info(frame.build("Software Installation Verification", rows))
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
        self._logger.info(f"{config['header_line']}")
        self._logger.info(
            f"| {'Package':<{config['name_width'] - 2}} | {'Version Information':<{config['version_width'] - 2}} | {'Status':<{config['status_width'] - 1}} |"
        )
        self._logger.info(f"{config['header_line']}")

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
            self._logger.info(f"{config['separator_line']}")

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

        self._logger.info(
            f"| {pkg:<{config['name_width'] - 2}} | {display_version:<{config['version_width'] - 2}} | {status:<{config['status_width'] - 2}} |"
        )
        self._logger.debug(f"Package '{pkg}' status: {status}")

    def _log_table_footer(self, config: dict[str, int]) -> None:
        """Log table footer.

        Args:
            config: Table configuration dictionary
        """
        self._logger.info(f"{config['header_line']}")

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

        self._logger.info(LogMsg.SW_PKG_TABLE_HEADER.value)
        self._logger.info(f"   {LogMsg.SW_PKG_TOTAL.value}: {total_packages}")
        self._logger.info(f"   {LogMsg.SW_PKG_SUCCESS.value}: {successful} ({success_rate:.1f}%)")
        if failed > 0:
            self._logger.info(
                f"   {LogMsg.SW_PKG_FAILED.value}: {failed} ({100 - success_rate:.1f}%)"
            )
            self._logger.warning(LogMsg.SW_PKG_MISSING_WARNING.value)
        else:
            self._logger.info(f"   {LogMsg.SW_PKG_ALL_INSTALLED.value}")
        self._logger.info("")

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
            self._logger.error(LogMsg.SW_PKG_NO_MANAGER.value)
            return False

        self._logger.info(LogMsg.SW_PKG_UPDATE.value)

        # Use appropriate update command based on package manager type
        if isinstance(self._package_manager, AptManager):
            self._logger.debug(LogMsg.SW_PKG_UPDATE_APT.value)
            success, _ = self._exec_cmd("sudo apt update -y")
        elif isinstance(self._package_manager, YumManager):
            self._logger.debug(LogMsg.SW_PKG_UPDATE_YUM.value)
            success, _ = self._exec_cmd("sudo yum check-update")
        else:
            self._logger.error(LogMsg.SW_PKG_UPDATE_UNKNOWN.value)
            return False

        if success:
            self._logger.info(LogMsg.SW_PKG_UPDATE_SUCCESS.value)
        else:
            self._logger.error(LogMsg.SW_PKG_UPDATE_FAIL.value)

        # await self.log_required_pakages_versions()

        return success
