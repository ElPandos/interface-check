#!/usr/bin/env python3
"""SLX Eye Scan Automation with SUT System Monitoring.

This script provides automated eye scan execution on SLX switches while
simultaneously monitoring system metrics on the SUT (System Under Test).

Features:
- Automated eye scans on SLX switch ports with configurable intervals
- Optional port toggling before scans
- Concurrent SUT system monitoring (mlxlink, temperature, etc.)
- Multi-hop SSH connections through jump hosts
- Graceful shutdown on Ctrl+C
- Comprehensive logging to separate log files

Usage:
    python main_eye_scan.py

Configuration:
    Edit main_eye_cfg.json to configure:
    - Jump host and target host credentials
    - SLX scan ports and intervals
    - SUT interfaces and scan intervals
    - Port toggling settings
"""

from dataclasses import dataclass
from datetime import UTC, datetime as dt
import json
import logging
from pathlib import Path
import re
import signal
import sys
import threading
import time

from src.core.connect import SshConnection
from src.core.helpers import get_attr_value
from src.core.parser import DmesgFlapParser, MlxlinkParser
from src.core.worker import Worker, WorkerConfig, WorkManager
from src.models.config import Host
from src.platform.enums.eye_scan_log import EyeScanLogMsg
from src.platform.enums.log import LogName
from src.platform.software_manager import SoftwareManager
from src.platform.tools import helper
from src.platform.tools.tool_factory import ToolFactory

# ============================================================================
# Graceful Shutdown Handling
# ============================================================================

# Global event for coordinating graceful shutdown across all threads
shutdown_event = threading.Event()


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown.

    Sets shutdown event to signal all threads to stop.
    Uses stderr since logger may not be initialized yet.
    """
    sys.stderr.write("Ctrl+C pressed. Shutting down gracefully...\n")
    shutdown_event.set()


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# Logging Configuration
# ============================================================================

# Create timestamped log directory
log_time_stamp = f"{dt.now().strftime('%Y%m%d_%H%M%S')}"
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Define separate log files for different components
main_log = log_dir / f"{log_time_stamp}_main.log"  # Main execution flow
memory_log = log_dir / f"{log_time_stamp}_memory.log"

sut_system_info_log = log_dir / f"{log_time_stamp}_sut_system_info.log"  # SUT system info
sut_mxlink_log = log_dir / f"{log_time_stamp}_sut_mxlink.log"  # SUT metrics
sut_mtemp_log = log_dir / f"{log_time_stamp}_sut_mtemp.log"  # SUT metrics
sut_link_flap_log = log_dir / f"{log_time_stamp}_sut_link_flap.log"  # SUT link status

slx_eye_log = log_dir / f"{log_time_stamp}_slx_eye.log"  # SLX eye scan


###########################
#
log_level = logging.INFO
#
###########################

# Log formatter with aligned log levels and logger names
log_format_string = "%(asctime)s - %(name)-30s - %(levelname)-8s - %(message)s"

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format_string,
    handlers=[
        logging.FileHandler(main_log),
        logging.StreamHandler(),
    ],
)

# Create loggers with handlers
logger_cfgs = [
    (LogName.CORE_MAIN.value, main_log),
    (LogName.CORE_MEMORY.value, memory_log),
    (LogName.SUT_SYSTEM_INFO.value, sut_system_info_log),
    (LogName.SUT_MXLINK.value, sut_mxlink_log),
    (LogName.SUT_MTEMP.value, sut_mtemp_log),
    (LogName.SUT_LINK_FLAP.value, sut_link_flap_log),
    (LogName.SLX_EYE.value, slx_eye_log),
]

for logger_name, log_file in logger_cfgs:
    logger = logging.getLogger(logger_name)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter(log_format_string))
    handler.setLevel(log_level)
    logger.addHandler(handler)
    logger.propagate = False

# Reference loggers for use in code
main_logger = logging.getLogger(LogName.CORE_MAIN.value)
memory_logger = logging.getLogger(LogName.CORE_MEMORY.value)
sut_system_info_logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)
sut_mxlink_logger = logging.getLogger(LogName.SUT_MXLINK.value)
sut_mtemp_logger = logging.getLogger(LogName.SUT_MTEMP.value)
sut_link_flap_logger = logging.getLogger(LogName.SUT_LINK_FLAP.value)
slx_eye_logger = logging.getLogger(LogName.SLX_EYE.value)


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from JSON.

    Contains all settings for:
    - Jump host connection
    - SLX switch connection and scan settings
    - SUT system connection and monitoring settings

    Attributes:
        jump_host/user/pass: Jump host credentials
        slx_*: SLX switch settings (host, ports, intervals, toggling)
        sut_*: SUT system settings (host, interfaces, packages, intervals)
    """

    jump_host: str
    jump_user: str
    jump_pass: str

    slx_host: str
    slx_user: str
    slx_pass: str
    slx_sudo_pass: str
    slx_scan_ports: list[str]
    slx_scan_interval: int
    slx_port_toggle_enabled: int
    slx_port_toggle_wait: int
    slx_port_eyescan_wait: int

    sut_host: str
    sut_user: str
    sut_pass: str
    sut_sudo_pass: str
    sut_scan_interfaces: list[str]
    sut_info_dump_level: int
    sut_required_software_packages: list[str]
    sut_scan_interval: int

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from nested JSON structure.

        Args:
            data: Dictionary with jump, slx, and sut configuration sections

        Returns:
            Config: Configured Config instance
        """
        j, slx, sut = data["jump"], data["slx"], data["sut"]
        return cls(
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            slx_host=slx["host"],
            slx_user=slx["user"],
            slx_pass=slx["pass"],
            slx_sudo_pass=slx["sudo_pass"],
            slx_scan_ports=slx["scan_ports"],
            slx_scan_interval=slx["scan_interval"],
            slx_port_toggle_enabled=slx["port_toggling_enabled"],
            slx_port_toggle_wait=slx["port_toggle_wait"],
            slx_port_eyescan_wait=slx["port_eye_scan_wait"],
            sut_host=sut["host"],
            sut_user=sut["user"],
            sut_pass=sut["pass"],
            sut_sudo_pass=sut["sudo_pass"],
            sut_scan_interfaces=sut["scan_interfaces"],
            sut_info_dump_level=sut["info_dump_level"],
            sut_required_software_packages=sut["required_software_packages"],
            sut_scan_interval=sut["scan_interval"],
        )


def load_cfg(logger: logging.Logger) -> Config:
    """Load configuration from JSON file.

    Args:
        logger: Logger instance for error reporting

    Returns:
        Config: Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file has invalid JSON
    """
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        config_file = Path(sys.executable).parent / "main_eye_cfg.json"
    else:
        # Running as script
        config_file = Path(__file__).parent / "main_eye_cfg.json"
    try:
        with config_file.open() as f:
            data = json.load(f)
        return Config.from_dict(data)
    except FileNotFoundError:
        logger.exception(f"Config file not found: {config_file}")
        logger.exception("Make sure config.json is in the same directory as the executable")
        raise
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in config file")
        raise


@dataclass
class EyeScanResult:
    """Eye scan result data.

    Attributes:
        interface: Interface name (e.g., 'xe1')
        port_id: Port identifier from cmsh
        result: Raw eye scan output from phy diag command
    """

    interface: str
    port_id: str
    result: str


class SlxEyeScanner:
    """Automated eye scan execution on SLX switches.

    Manages SSH connection to SLX switch, performs interface lookups,
    executes eye scans with optional port toggling, and collects results.

    The scanner:
    1. Connects to SLX via jump host
    2. Maps interface names to port IDs
    3. Optionally toggles ports before scanning
    4. Executes eye scan commands
    5. Collects and stores results
    """

    def __init__(self, cfg: Config, logger: logging.Logger):
        """Initialize SLX eye scanner.

        Args:
            cfg: Configuration object
            logger: Logger instance for this scanner
        """
        self._cfg = cfg
        self._results: list[EyeScanResult] = []
        self._interface_cache: dict[str, tuple[str, str]] = {}
        self._ssh: SshConnection | None = None

        self._logger = logger

    def _exec_with_logging(self, cmd: str, cmd_description: str = "") -> str:
        """Execute shell command with automatic pre/post logging.

        Args:
            cmd: Command to execute
            cmd_description: Optional description for logging (defaults to cmd)

        Returns:
            str: Command output
        """
        log_cmd = cmd_description if cmd_description else cmd
        self._logger.debug(f"{EyeScanLogMsg.CMD_EXECUTING.value}: '{log_cmd}'")
        result = self._ssh.exec_shell_command(cmd)
        self._logger.debug(f"{EyeScanLogMsg.CMD_RESULT.value}:\n{result}")
        return result

    def connect(self) -> bool:
        """Establish SSH connection and setup SLX environment.

        Connects via jump host, opens shell, enters Linux shell mode,
        and elevates to root user. Stays in Linux shell for cmsh commands.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._logger.info(f"Connecting to SLX host: {self._cfg.slx_host}")
            self._logger.debug(f"Using jump host: {self._cfg.jump_host}")
            self._ssh = _create_ssh_connection(self._cfg, "slx")

            if not self._ssh.connect():
                self._logger.error(EyeScanLogMsg.SSH_CONN_FAILED.value)
                return False
            self._logger.debug("SSH connection established")

            if not self._ssh.open_shell():
                self._logger.error(EyeScanLogMsg.SHELL_OPEN_FAILED.value)
                return False
            self._logger.debug("Shell opened successfully")

            # --------------------- Setup shell environment on SLX OS -------------------- #

            # Enter Linux shell
            self._exec_with_logging("start-shell")

            # Switch to root user
            self._exec_with_logging("su root")

            # Provide password
            self._logger.debug("Providing sudo password")
            result = self._exec_with_logging(self._cfg.slx_sudo_pass, "password")
            self._logger.debug(f"Password authentication result: {result}")

            # Don't enter fbr-CLI yet - need to run cmsh first from Linux shell
            self._logger.info(f"{EyeScanLogMsg.SSH_CONN_SUCCESS.value} (in Linux shell)")
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception("Connection failed")
            return False

    def get_port_id(self, interface: str) -> str | None:
        """Extract port ID from cmsh output.

        Runs cmsh command in Linux shell to query interface database.
        Parses output to extract numeric port ID.

        Args:
            interface: Interface name (e.g., 'enp1s0f0')

        Returns:
            str | None: Port ID string if found, None otherwise
        """
        if not self._ssh:
            self._logger.error(EyeScanLogMsg.SSH_NO_CONN.value)
            return None

        # cmsh must run from Linux shell, not fbr-CLI
        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"

        try:
            result = self._exec_with_logging(cmd, f"cmsh for interface '{interface}'")

            # Pattern: interface_name 0xHEX number port_id
            pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
            self._logger.debug(f"Searching with pattern: '{pattern}'")
            match = re.search(pattern, result)

            if match:
                port_id = match.group(1)
                self._logger.info(
                    f"{EyeScanLogMsg.PORT_ID_FOUND.value} '{port_id}' for interface: '{interface}'"
                )
                return port_id
            self._logger.warning(f"{EyeScanLogMsg.PORT_ID_NOT_FOUND.value} '{interface}'")
            return None  # noqa: TRY300
        except Exception:
            self._logger.exception(f"Failed to get port ID for '{interface}'")
            return None

    def _enter_fbr_cli(self, purpose: str = "") -> None:
        """Enter fbr-CLI from Linux shell.

        Args:
            purpose: Optional description of why entering fbr-CLI (for logging)
        """
        if purpose:
            self._logger.info(f"{EyeScanLogMsg.FBR_ENTERING.value} {purpose}")
        else:
            self._logger.info(EyeScanLogMsg.FBR_ENTERING.value)
        self._logger.debug(f"{EyeScanLogMsg.CMD_EXECUTING.value}: 'fbr-CLI'")
        self._ssh.exec_shell_command("fbr-CLI")
        time.sleep(0.5)  # Allow prompt to stabilize

        # Read and log the fbr-CLI welcome message from buffer
        welcome_msg = self._ssh.exec_shell_command("")
        self._logger.debug(f"{EyeScanLogMsg.CMD_RESULT.value}:\n{welcome_msg}")
        self._logger.info("Entered fbr-CLI successfully")

    def _exit_fbr_cli(self) -> None:
        """Exit fbr-CLI back to Linux shell using Ctrl+C.

        Sends Ctrl+C character to exit fbr-CLI and return to Linux shell.
        """
        self._logger.info("Sending 'Ctrl+C' to exit fbr-CLI")
        self._exec_with_logging("\x03", "Ctrl+C")  # Send Ctrl+C
        time.sleep(0.3)
        self._logger.info(EyeScanLogMsg.FBR_EXITED.value)

    def get_interface_name(self, port_id: str) -> str | None:
        """Find interface name by port ID in fbr-CLI.

        Enters fbr-CLI, runs 'ps' command, parses output for interface mapping,
        then exits back to Linux shell.

        Args:
            port_id: Port identifier from cmsh

        Returns:
            str | None: Interface name (e.g., 'xe1') if found, None otherwise

        Example:
            ps output: "xe1(10)" -> returns 'xe1'
        """
        if not self._ssh:
            self._logger.error(EyeScanLogMsg.SSH_NO_CONN.value)
            return None

        try:
            # Enter fbr-CLI from Linux shell
            self._enter_fbr_cli(f"to find interface for port {port_id}")

            # Run ps command in fbr-CLI
            ps_result = self._exec_with_logging("ps")

            # Exit fbr-CLI back to Linux shell
            self._exit_fbr_cli()

            # Pattern matches: interface_name(port_id)
            # Example: xe1(10) captures 'xe1'
            pattern = rf"(\w+)\(\s*{re.escape(port_id)}\s*\)"
            self._logger.debug(f"Searching with pattern: '{pattern}'")
            match = re.search(pattern, ps_result)

            if match:
                interface_name = match.group(1)
                self._logger.info(
                    f"{EyeScanLogMsg.INTERFACE_FOUND.value} '{interface_name}' for port: '{port_id}'"
                )
                return interface_name
            self._logger.warning(f"{EyeScanLogMsg.INTERFACE_NOT_FOUND.value}: '{port_id}'")
            return None  # noqa: TRY300
        except Exception:
            self._logger.exception(f"Failed to get interface name for port: '{port_id}'")
            return None

    def enable_interface(self, port_name: str) -> None:
        """Enable interface via fbr-CLI port command.

        Args:
            port_name: Interface name (e.g., 'xe1')
        """
        command = f"port {port_name} enable=true"
        self._execute_toggle(command)

    def disable_interface(self, port_name: str) -> None:
        """Disable interface via fbr-CLI port command.

        Args:
            port_name: Interface name (e.g., 'xe1')
        """
        command = f"port {port_name} enable=false"
        self._execute_toggle(command)

    def _execute_toggle(self, cmd: str) -> None:
        """Execute port toggle command in fbr-CLI.

        Enters fbr-CLI, runs toggle command, exits back to Linux shell,
        and waits for toggle to take effect.

        Args:
            cmd: Port toggle command (e.g., 'port xe1 enable=true')
        """
        if not self._ssh:
            self._logger.error(f"{EyeScanLogMsg.SSH_NO_CONN.value} for toggle")
            return

        try:
            # Enter fbr-CLI for toggle command
            self._enter_fbr_cli("for toggle")

            self._logger.debug(f"{EyeScanLogMsg.TOGGLE_EXECUTING.value}: '{cmd}'")
            self._exec_with_logging(cmd)

            # Exit fbr-CLI back to Linux shell
            self._exit_fbr_cli()

            self._logger.debug(
                f"{EyeScanLogMsg.TOGGLE_WAITING.value}: {self._cfg.slx_port_toggle_wait} seconds..."
            )
            time.sleep(self._cfg.slx_port_toggle_wait)

        except Exception:
            self._logger.exception(f"{EyeScanLogMsg.TOGGLE_FAILED.value} '{cmd}'")

    def run_eye_scan(self, interface: str, port_id: str) -> None:
        """Execute eye scan with optional interface toggle.

        Optionally toggles port, enters fbr-CLI, runs phy diag eyescan command,
        collects results, and exits back to Linux shell.

        Args:
            interface: Interface name (e.g., 'xe1')
            port_id: Port identifier for logging
        """
        if not self._ssh:
            self._logger.error(f"{EyeScanLogMsg.SSH_NO_CONN.value} for eye scan")
            return

        try:
            self._logger.info(
                f"{EyeScanLogMsg.EYE_SCAN_START.value} '{interface}' (Port: '{port_id}')"
            )

            if self._cfg.slx_port_toggle_enabled:
                self._logger.info(EyeScanLogMsg.TOGGLE_ENABLED.value)
                self.disable_interface(interface)
                self.enable_interface(interface)

            # Enter fbr-CLI for eye scan
            self._enter_fbr_cli("for eye scan")

            # Clear buffer before eye scan
            self._logger.info("Clearing buffer before eye scan")
            self._ssh.clear_shell()
            self._logger.info("Buffer cleared")

            # Send eye scan command
            cmd = f"phy diag {interface} eyescan"
            self._logger.info(f"{EyeScanLogMsg.CMD_EXECUTING.value} eye scan: '{cmd}'")
            self._ssh.exec_shell_command(cmd + "\n", until_prompt=False)

            # Wait for eye scan to complete
            self._logger.info(f"Waiting {self._cfg.slx_port_eyescan_wait}s for eye scan")
            time.sleep(self._cfg.slx_port_eyescan_wait)

            # Get results
            result = self._ssh.exec_shell_command("\n")

            self._results.append(EyeScanResult(interface, port_id, result))
            self._logger.info(
                f"{EyeScanLogMsg.EYE_SCAN_COMPLETE.value}: '{interface}' (Port: '{port_id}')"
            )
            self._logger.info("=======================================")
            self._logger.info("\n%s", self._results[-1].result)
            self._logger.info("=======================================")

            # Exit fbr-CLI back to Linux shell
            self._exit_fbr_cli()

        except Exception:
            self._logger.exception(f"{EyeScanLogMsg.EYE_SCAN_FAILED.value} for '{interface}'")

    def _lookup_interface_mapping(self, interface: str) -> tuple[str, str] | None:
        """Lookup port ID and interface name for given interface.

        Args:
            interface: Interface name to lookup

        Returns:
            tuple[str, str] | None: Tuple of (port_id, interface_name) if found, None otherwise
        """
        self._logger.info(f"{EyeScanLogMsg.INTERFACE_LOOKUP.value} for '{interface}'")

        port_id = self.get_port_id(interface)
        if not port_id:
            self._logger.error(
                f"{EyeScanLogMsg.PORT_ID_NOT_FOUND.value} '{interface}', {EyeScanLogMsg.SCAN_SKIPPING.value}"
            )
            return None

        interface_name = self.get_interface_name(port_id)
        if not interface_name:
            self._logger.error(
                f"{EyeScanLogMsg.INTERFACE_NOT_FOUND.value} '{port_id}', {EyeScanLogMsg.SCAN_SKIPPING.value}"
            )
            return None

        return (port_id, interface_name)

    def scan_interfaces(self, interfaces: list[str]) -> bool:
        """Complete eye scan workflow for multiple interfaces.

        For each interface:
        1. Check cache for interface mapping
        2. If not cached, lookup port ID and interface name
        3. Execute eye scan
        4. Cache successful mappings

        Args:
            interfaces: List of interface names to scan

        Returns:
            bool: True if at least one scan succeeded, False otherwise
        """
        self._logger.debug(f"Scan interfaces called with: {interfaces}")
        if not interfaces:
            self._logger.warning(EyeScanLogMsg.SCAN_NO_INTERFACES.value)
            return True

        self._logger.info(
            f"{EyeScanLogMsg.SCAN_START.value}: {len(interfaces)} interfaces: {interfaces}"
        )
        success_count = 0

        for interface in interfaces:
            self._logger.debug(f"{EyeScanLogMsg.SCAN_PROCESSING.value}: '{interface}'")
            try:
                # Check cache first
                if interface in self._interface_cache:
                    port_id, interface_name = self._interface_cache[interface]
                    self._logger.debug(
                        f"{EyeScanLogMsg.CACHE_HIT.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
                    )
                else:
                    # First time lookup
                    mapping = self._lookup_interface_mapping(interface)
                    if not mapping:
                        continue

                    port_id, interface_name = mapping
                    # Cache the mapping
                    self._interface_cache[interface] = (port_id, interface_name)
                    self._logger.info(
                        f"{EyeScanLogMsg.CACHE_MISS.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
                    )

                self.run_eye_scan(interface_name, port_id)
                success_count += 1

            except Exception:
                self._logger.exception(f"Failed to scan interface '{interface}'")
                continue

        self._logger.info(f"{EyeScanLogMsg.SCAN_COMPLETE.value}: {success_count}/{len(interfaces)}")
        return success_count > 0

    def disconnect(self) -> None:
        """Clean up connection."""
        if self._ssh:
            self._ssh.disconnect()

    def scans_collected(self) -> int:
        """Return number of scans collected.

        Returns:
            int: Number of eye scans collected
        """
        return len(self._results)


class SutSystemScanner:
    """System monitoring and data collection for SUT (System Under Test).

    Manages SSH connection to SUT system, installs required software,
    logs system information, and runs background workers to collect
    network metrics (mlxlink, temperature, etc.).

    The scanner:
    1. Connects to SUT via jump host
    2. Installs required packages (mlxlink, mst, etc.)
    3. Logs system information
    4. Starts worker threads for continuous metric collection
    """

    def __init__(self, cfg: Config, logger: logging.Logger):
        """Initialize SUT system scanner.

        Args:
            cfg: Configuration object
            logger: Logger instance for this scanner
        """
        self._cfg = cfg
        self._ssh: SshConnection | None = None
        self._software_manager: SoftwareManager | None = None
        self._worker_manager = WorkManager()

        self._logger = logger

    def _exec_with_logging(self, cmd: str, logger: logging.Logger) -> tuple[str, int]:
        """Execute command with automatic pre/post logging.

        Args:
            cmd: Command to execute
            logger: Logger instance to use

        Returns:
            tuple[str, int]: Tuple of (stdout, return_code)
        """
        logger.debug(f"{EyeScanLogMsg.CMD_EXECUTING.value}: '{cmd}'")
        result = self._ssh.exec_cmd(cmd)
        logger.debug(f"{EyeScanLogMsg.CMD_RESULT.value}:\n{result.stdout}")
        return result.stdout, result.rcode

    def connect(self) -> bool:
        """Establish SSH connection and initialize software manager.

        Connects via jump host, tests connection with basic commands,
        and initializes software manager for package operations.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._logger.info(f"Connecting to host: {self._cfg.sut_host}")
            self._logger.debug(f"Using jump host: {self._cfg.jump_host}")
            self._ssh = _create_ssh_connection(self._cfg, "sut")

            if not self._ssh.connect():
                self._logger.error(EyeScanLogMsg.SSH_CONN_FAILED.value)
                return False
            self._logger.debug("SSH connection established")

            # Shell not needed for system scanner - using execute_command instead
            self._logger.debug("Skipping shell opening (using exec_cmd instead)")

            # Test connection with simple commands
            test_commands = ["whoami", "pwd"]
            self._logger.debug(f"Testing connection with commands: {test_commands}")

            for cmd in test_commands:
                stdout, rcode = self._exec_with_logging(cmd, self._logger)  # noqa: RUF059
                if rcode != 0:
                    result = self._ssh.exec_cmd(cmd)
                    self._logger.warning(f"Command '{cmd}' failed (rc={rcode}): {result.stderr}")

            # Initialize software manager
            try:
                self._logger.debug("Initializing software manager")
                self._software_manager = SoftwareManager(self._ssh)
                self._logger.debug(EyeScanLogMsg.SW_MGR_INIT.value)
            except Exception:
                self._logger.exception(EyeScanLogMsg.SW_MGR_INIT_FAILED.value)
                self._software_manager = None

            self._logger.info(EyeScanLogMsg.SSH_CONN_SUCCESS.value)
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception("Connection failed")
            return False

    def install_required_software(self) -> bool:
        """Install required software packages via software manager.

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._software_manager:
            self._logger.error(EyeScanLogMsg.SW_MGR_NOT_INIT.value)
            return False

        try:
            self._logger.info(EyeScanLogMsg.SW_INSTALL_START.value)
            self._logger.debug(f"Packages to install: {self._cfg.sut_required_software_packages}")
            result = self._software_manager.install_required_packages(
                self._cfg.sut_required_software_packages
            )
            self._logger.info(f"{EyeScanLogMsg.SW_INSTALL_COMPLETE.value}: {result}")
            return result  # noqa: TRY300
        except Exception:
            self._logger.exception(EyeScanLogMsg.SW_INSTALL_FAILED.value)
            return False

    def log_required_software_versions(self) -> bool:
        """Log versions of required software packages.

        Returns:
            bool: True if logging successful, False otherwise
        """
        if not self._software_manager:
            self._logger.error(EyeScanLogMsg.SW_MGR_NOT_INIT.value)
            return False
        try:
            self._logger.info(EyeScanLogMsg.SW_VERSION_LOG.value)
            self._logger.debug(f"Packages to check: {self._cfg.sut_required_software_packages}")
            self._software_manager.log_required_package_versions(
                self._cfg.sut_required_software_packages
            )
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception(EyeScanLogMsg.SW_VERSION_FAILED.value)
            return False

    def log_system_info(self, logger: logging.Logger) -> None:
        """Log system information using available tools.

        Iterates through all available tools from ToolFactory,
        executes them, and logs their output.

        Args:
            logger: Logger instance for tool output
        """
        try:
            self._logger.info(EyeScanLogMsg.SYS_INFO_LOG.value)
            available_tools = ToolFactory.get_available_tools()
            self._logger.debug(f"Available tools: {available_tools}")

            for tool_type in available_tools:
                self._logger.debug(f"Executing tool: {tool_type}")
                tool = ToolFactory.create_tool(
                    tool_type=tool_type,
                    ssh=self._ssh,
                    interfaces=self._cfg.sut_scan_interfaces,
                )
                tool.execute()
                tool.log(logger)
                self._logger.debug(f"Tool {tool_type} completed")
        except Exception:
            self._logger.exception(EyeScanLogMsg.SYS_INFO_FAILED.value)

    def run_scanners(self, cfg: Config) -> bool:
        """Start background worker threads for metrics collection.

        Creates 3 workers per interface:
        1. mlxlink - Network metrics (temp, voltage, power, BER)
        2. mget_temp - NIC temperature
        3. dmesg - Link flap detection

        Args:
            cfg: Configuration containing interfaces to scan

        Returns:
            bool: True if workers started successfully, False otherwise
        """
        try:
            self._logger.info(EyeScanLogMsg.WORKER_START.value)
            self._logger.debug(f"Creating workers for interfaces: {cfg.sut_scan_interfaces}")

            for interface in cfg.sut_scan_interfaces:
                self._logger.debug(f"Setting up workers for interface: '{interface}'")
                pci_id = helper.get_pci_id(self._ssh, interface)
                self._logger.debug(f"PCI ID for '{interface}': '{pci_id}'")

                # self._create_mlxlink_worker(pci_id)
                # self._create_mtemp_worker(pci_id)
                self._create_dmesg_worker(interface)

            self._logger.info(f"Created {len(cfg.sut_scan_interfaces) * 3} workers")
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception(EyeScanLogMsg.WORKER_FAILED.value)
            return False

    def _create_mlxlink_worker(self, pci_id: str) -> None:
        """Create mlxlink worker for network metrics.

        Args:
            pci_id: PCI device ID
        """
        attributes = [
            "temperature",
            "voltage",
            "bias_current",
            "rx_power",
            "tx_power",
            "time_since_last_clear",
            "effective_physical_errors",
            "effective_physical_ber",
            "raw_physical_errors_per_lane",
            "raw_physical_ber",
        ]

        worker_cfg = WorkerConfig()
        worker_cfg.command = f"mlxlink -d {pci_id} -e -m -c"
        worker_cfg.parser = MlxlinkParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = sut_mxlink_logger

        self._add_worker_to_manager(worker_cfg)

    def _create_mtemp_worker(self, pci_id: str) -> None:
        """Create temperature worker for NIC temperature.

        Args:
            pci_id: PCI device ID
        """
        worker_cfg = WorkerConfig()
        worker_cfg.command = f"mget_temp -d {pci_id}"
        worker_cfg.parser = None
        worker_cfg.logger = sut_mtemp_logger

        self._add_worker_to_manager(worker_cfg)

    def _create_dmesg_worker(self, interface: str) -> None:
        """Create dmesg worker for link status monitoring.

        Args:
            interface: Network interface name
        """
        attributes = [
            "interface",
            "down_timestamp",
            "up_timestamp",
            "duration",
        ]

        worker_cfg = WorkerConfig()
        worker_cfg.command = f'dmesg --time-format iso | grep -i "{interface}.*link" | tail -100'
        worker_cfg.parser = DmesgFlapParser(dt.now(UTC))
        worker_cfg.attributes = attributes
        worker_cfg.logger = sut_link_flap_logger

        self._add_worker_to_manager(worker_cfg)

    def _add_worker_to_manager(self, worker_cfg: WorkerConfig) -> None:
        self._logger.debug(f"Worker command: '{worker_cfg.command}'")
        self._worker_manager.add(Worker(worker_cfg, self._cfg, self._ssh))

    @property
    def worker_manager(self) -> WorkManager:
        """Get worker manager instance.

        Returns:
            WorkManager: Worker manager for this scanner
        """
        return self._worker_manager

    def disconnect(self) -> None:
        """Clean up connection."""
        if self._ssh:
            self._ssh.disconnect()


def _create_ssh_connection(cfg: Config, host_type: str) -> SshConnection:
    """Create SSH connection with jump host.

    Args:
        cfg: Configuration object
        host_type: Either 'slx' or 'sut' to determine which host to connect to

    Returns:
        SshConnection: Configured SshConnection object (not yet connected)
    """
    jump_host = Host(
        ip=cfg.jump_host,
        username=cfg.jump_user,
        password=cfg.jump_pass,
    )

    if host_type == "slx":
        return SshConnection(
            host=cfg.slx_host,
            username=cfg.slx_user,
            password=cfg.slx_pass,
            jump_hosts=[jump_host],
        )
    # sut
    return SshConnection(
        host=cfg.sut_host,
        username=cfg.sut_user,
        password=cfg.sut_pass,
        jump_hosts=[jump_host],
        sudo_pass=cfg.sut_sudo_pass,
    )


def main():  # noqa: PLR0912, PLR0915
    """Main execution orchestrating SUT monitoring and SLX eye scans.

    Execution flow:
    1. Load configuration from JSON
    2. Initialize and connect SUT system scanner
    3. Start SUT metric collection workers
    4. Initialize and connect SLX eye scanner
    5. Run continuous eye scan loop until Ctrl+C
    6. Extract and log collected samples
    7. Graceful shutdown of all components

    The function runs until interrupted by Ctrl+C, at which point it
    performs graceful shutdown of all threads and connections.
    """
    _logger = main_logger

    try:
        _logger.debug("Loading configuration from file")
        cfg = load_cfg(_logger)
        _logger.info(EyeScanLogMsg.CONFIG_LOADED.value)
        _logger.debug(f"SLX host: {cfg.slx_host}, SUT host: {cfg.sut_host}")
    except Exception:
        _logger.exception(EyeScanLogMsg.CONFIG_FAILED.value)
        return

    _logger.debug("Initializing scanners")

    slx_eye_scanner = SlxEyeScanner(cfg, slx_eye_logger)
    sut_system_scanner = SutSystemScanner(cfg, main_logger)

    try:
        _logger.info(EyeScanLogMsg.SCANNER_INIT.value)
        if not sut_system_scanner.connect():
            _logger.error(EyeScanLogMsg.SCANNER_CONN_FAILED.value)
            return

        # ---------------------------------------------------------------------------- #
        #                           Install required software                          #
        # ---------------------------------------------------------------------------- #

        # if not sut_system_scanner.install_required_software():
        #    _logger.warning("Failed to install required software, continuing anyway")

        # if not sut_system_scanner.log_required_software_versions():
        #    _logger.warning("Failed to log installed software versions")

        # ---------------------------------------------------------------------------- #
        #                            Log system information                            #
        # ---------------------------------------------------------------------------- #

        # _logger.info(f"Start system information scan. Logs saved to: {sut_system_info_log}")

        # if not sut_system_scanner.log_system_info(sut_system_info_logger):
        #    _logger.warning("Failed to log system information")

        # ---------------------------------------------------------------------------- #
        #                         Start system scanning threads                        #
        # ---------------------------------------------------------------------------- #

        _logger.info(f"Scanning interfaces: {cfg.sut_scan_interfaces}")

        if not sut_system_scanner.run_scanners(cfg):
            _logger.warning("System scanning failed to start")

    except Exception:
        _logger.exception("System scanner failed")

    # ---------------------------------------------------------------------------- #
    #                              Start eye scanning                              #
    # ---------------------------------------------------------------------------- #

    _logger.info(f"Start eye scan automation. Logs saved to: {slx_eye_log}")
    _logger.info(f"Scanning ports: {cfg.slx_scan_ports}")
    _logger.info("Press Ctrl+C to stop the program")

    try:
        if not slx_eye_scanner.connect():
            _logger.error("Failed to connect to SLX eye scanner")
            return

        scan_count = 0
        while not shutdown_event.is_set():
            try:
                _logger.info(f"Start scan iteration #{scan_count + 1}")
                # Scan ports in config
                if slx_eye_scanner.scan_interfaces(cfg.slx_scan_ports):
                    scan_count += 1
                    _logger.info(f"Completed scan #{scan_count}")
                else:
                    _logger.warning(f"Scan iteration #{scan_count + 1} failed")

                # Wait before next scan (check shutdown every second for responsiveness)
                if not shutdown_event.is_set():
                    _logger.info(f"Waiting {cfg.slx_scan_interval} seconds before next scan...")
                    for _ in range(cfg.slx_scan_interval):
                        if shutdown_event.is_set():
                            _logger.info(EyeScanLogMsg.SHUTDOWN_SIGNAL.value)
                            break
                        time.sleep(1)

            except Exception:
                _logger.exception("Scan iteration failed")
                if not shutdown_event.is_set():
                    _logger.info("Waiting 5 seconds before retry...")
                    time.sleep(5)  # Brief pause before retry

    except KeyboardInterrupt:
        _logger.info("Keyboard interrupt received in main loop")
    except Exception:
        _logger.exception("Main execution failed")
    finally:
        _logger.info("=" * 60)
        _logger.info(EyeScanLogMsg.SHUTDOWN_START.value)
        _logger.info("=" * 60)

        _logger.info(EyeScanLogMsg.SHUTDOWN_EYE_SCANNER.value)
        slx_eye_scanner.disconnect()
        _logger.debug("Eye scanner disconnected")

        _logger.info(EyeScanLogMsg.WORKER_EXTRACT.value)
        workers = sut_system_scanner.worker_manager.get_workers_in_pool()
        _logger.debug(f"Found {len(workers)} workers to extract samples from")
        for w in workers:
            w.extract_all_samples()

        # Build matrix with smallest list determining rows
        all_samples = [w.get_extracted_samples() for w in workers]
        min_rows = min(len(samples) for samples in all_samples) if all_samples else 0

        if min_rows > 0:
            # CSV headers - begin_timestamp first
            headers = [
                "begin_timestamp",
                "temperature",
                "voltage",
                "bias_current",
                "rx_power",
                "tx_power",
                "time_since_last_clear",
                "effective_physical_errors",
                "effective_physical_ber",
                "raw_physical_errors_per_lane",
                "raw_physical_ber",
                "m_temp_nic",
                "link_status",
                "link_status_timestamp",
            ]
            headers_str = [",".join(headers)]

            # mlxlink attributes (excluding begin - we add it first)
            mlxlink_attrs = [
                "temperature",
                "voltage",
                "bias_current",
                "rx_power",
                "tx_power",
                "time_since_last_clear",
                "effective_physical_errors",
                "effective_physical_ber",
                "raw_physical_errors_per_lane",
                "raw_physical_ber",
            ]

            for i in range(min_rows):
                row = []
                for worker_idx, samples in enumerate(all_samples):
                    sample = samples[i]
                    if worker_idx == 0:  # Worker 1: mlxlink
                        # Add begin timestamp first (from Sample, not snapshot)
                        # Format: YYYY-MM-DD HH:MM:SS.mmm
                        timestamp = (
                            sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            if sample.begin
                            else ""
                        )
                        row.append(timestamp)
                        # Add all other mlxlink metrics
                        row.extend(get_attr_value(sample.snapshot, attr) for attr in mlxlink_attrs)
                    elif worker_idx == 1:  # Worker 2: NIC temp
                        row.append(str(sample.snapshot) if hasattr(sample, "snapshot") else "")
                    elif worker_idx == 2:  # Worker 3: dmesg link status
                        dmesg_output = str(sample.snapshot) if hasattr(sample, "snapshot") else ""
                        parser = DmesgFlapParser(dmesg_output)
                        link_status, link_ts = parser.get_most_recent_status()
                        row.extend([link_status, link_ts])
                headers_str.append(",".join(row))

            _logger.info("\n%s\n", "\n".join(headers_str))

        _logger.info(EyeScanLogMsg.WORKER_SHUTDOWN.value)

        _logger.debug("Stopping all workers")
        sut_system_scanner.worker_manager.stop_all()

        _logger.debug("Disconnecting system scanner")
        sut_system_scanner.disconnect()

    _logger.info(f"Total eye scans completed: {slx_eye_scanner.scans_collected()}")
    _logger.info("Logs saved to:")
    for label, path in [
        ("Main", main_log),
        ("System info", sut_system_info_log),
        ("mxlink scan", sut_mxlink_log),
        ("m_temp scan", sut_mtemp_log),
        ("link_status scan", sut_link_flap_log),
        ("SLX eye scan", slx_eye_log),
    ]:
        _logger.info(f"{label}: {path}")


if __name__ == "__main__":
    main()
