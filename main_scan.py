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
    python main_scan.py

Configuration:
    Edit main_scan_cfg.json to configure:
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
import signal
import sys
import threading
import time

from src.core.cli import PrettyFrame
from src.core.connect import LocalConnection, SshConnection
from src.core.enums.connect import ConnectType, HostType, ShowPartType
from src.core.enums.messages import LogMsg
from src.core.helpers import get_attr_value
from src.core.logging_setup import initialize_logging
from src.core.parser import DmesgFlapParser, EthtoolModuleParser, MlxlinkAmberParser, MlxlinkParser
from src.core.worker import Worker, WorkerConfig, WorkManager
from src.models.config import Host
from src.platform.software_manager import SoftwareManager
from src.platform.tools import helper
from src.platform.tools.slx_eye_scanner import SlxEyeScanner
from src.platform.tools.tool_factory import ToolFactory

# ============================================================================
# Graceful Shutdown Handling
# ============================================================================

# Global event for coordinating graceful shutdown across all threads
shutdown_event = threading.Event()


def signal_handler(_signum, _frame) -> None:
    """Handle Ctrl+C signal for graceful shutdown.

    Sets shutdown event to trigger cleanup in finally block.
    """
    frame = PrettyFrame()
    msg = frame.build("SHUTDOWN SIGNAL", ["Ctrl+C pressed. Shutting down gracefully..."])
    sys.stderr.write(f"\n{msg}\n")
    shutdown_event.set()


# Register signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# Logging Configuration
# ============================================================================

loggers = initialize_logging()
main_logger = loggers["main"]
sut_system_info_logger = loggers["sut_system_info"]
sut_mxlink_logger = loggers["sut_mxlink"]
sut_mxlink_amber_logger = loggers["sut_mxlink_amber"]
sut_mtemp_logger = loggers["sut_mtemp"]
sut_ethtool_logger = loggers["sut_ethtool"]
sut_link_flap_logger = loggers["sut_link_flap"]
slx_eye_logger = loggers["slx_eye"]
log_dir = loggers["log_dir"]


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

    log_level: str

    jump_host: str
    jump_user: str
    jump_pass: str

    slx_host: str
    slx_user: str
    slx_pass: str
    slx_sudo_pass: str
    slx_scan_ports: list[str]
    slx_scan_interval_sec: int
    slx_port_toggle_enabled: bool
    slx_port_toggle_wait_sec: int
    slx_port_eyescan_wait_sec: int

    sut_host: str
    sut_user: str
    sut_pass: str
    sut_sudo_pass: str
    sut_scan_interfaces: list[str]
    sut_connect_type: ConnectType
    sut_show_parts: list[ShowPartType]
    sut_time_cmd: bool
    sut_required_software_packages: list[str]
    sut_scan_interval_low_res_ms: int
    sut_scan_interval_high_res_ms: int
    sut_scan_max_log_size_kb: int

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
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            jump_pass=j["pass"],
            slx_host=slx["host"],
            slx_user=slx["user"],
            slx_pass=slx["pass"],
            slx_sudo_pass=slx["sudo_pass"],
            slx_scan_ports=slx["scan_ports"],
            slx_scan_interval_sec=slx["scan_interval_sec"],
            slx_port_toggle_enabled=slx["port_toggling_enabled"],
            slx_port_toggle_wait_sec=slx["port_toggle_wait_sec"],
            slx_port_eyescan_wait_sec=slx["port_eye_scan_wait_sec"],
            sut_host=sut["host"],
            sut_user=sut["user"],
            sut_pass=sut["pass"],
            sut_sudo_pass=sut["sudo_pass"],
            sut_scan_interfaces=sut["scan_interfaces"],
            sut_connect_type=ConnectType(sut.get("connect_type", "local")),
            sut_show_parts=[ShowPartType(p) for p in sut.get("show_parts", [])],
            sut_time_cmd=sut.get("time_cmd", False),
            sut_required_software_packages=sut["required_software_packages"],
            sut_scan_interval_low_res_ms=sut["scan_interval_low_res_ms"],
            sut_scan_interval_high_res_ms=sut["scan_interval_high_res_ms"],
            sut_scan_max_log_size_kb=sut["scan_max_log_size_kb"],
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
    logger.debug(LogMsg.CONFIG_START)

    cfg_name = "main_scan_cfg.json"
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        config_file = Path(sys.executable).parent / cfg_name
    else:
        # Running as script
        config_file = Path(__file__).parent / cfg_name
    try:
        with config_file.open() as f:
            data = json.load(f)

        logger.info(LogMsg.CONFIG_LOADED.value)

        return Config.from_dict(data)
    except FileNotFoundError:
        logger.exception(f"{LogMsg.MAIN_CONFIG_NOT_FOUND.value}: {config_file}")
        logger.exception(LogMsg.MAIN_CONFIG_SAME_DIR.value)
        raise
    except json.JSONDecodeError:
        logger.exception(LogMsg.MAIN_CONFIG_INVALID_JSON.value)
        raise


class SlxEyeScannerWrapper:
    """Wrapper for SlxEyeScanner with connection management."""

    def __init__(self, cfg: Config, logger: logging.Logger):
        """Initialize wrapper.

        Args:
            cfg: Configuration object
            logger: Logger instance
        """
        self._cfg = cfg
        self._logger = logger
        self._ssh: SshConnection | None = None
        self._scanner: SlxEyeScanner | None = None

    def connect(self) -> bool:
        """Establish SSH connection and setup SLX environment.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._logger.info(f"Connecting to SLX host: {self._cfg.slx_host}")
            self._logger.debug(f"Using jump host: {self._cfg.jump_host}")
            self._ssh = _create_ssh_connection(self._cfg, HostType.SLX)

            if not self._ssh.connect():
                self._logger.error(LogMsg.SSH_CONN_FAILED.value)
                return False
            self._logger.debug(LogMsg.MAIN_SSH_ESTABLISHED.value)

            self._scanner = SlxEyeScanner(self._ssh, self._logger)
            return self._scanner.setup_shell(self._cfg.slx_sudo_pass)
        except Exception:
            self._logger.exception(LogMsg.MAIN_CONN_FAILED.value)
            return False

    def scan_interfaces(self, interfaces: list[str]) -> bool:
        """Scan interfaces using SlxEyeScanner.

        Args:
            interfaces: List of interface names to scan

        Returns:
            bool: True if at least one scan succeeded
        """
        if not self._scanner:
            self._logger.error("Scanner not initialized")
            return False

        return self._scanner.scan_interfaces(
            interfaces,
            toggle_enabled=self._cfg.slx_port_toggle_enabled,
            toggle_wait_sec=self._cfg.slx_port_toggle_wait_sec,
            scan_wait_sec=self._cfg.slx_port_eyescan_wait_sec,
        )

    def disconnect(self) -> None:
        """Clean up connection."""
        if self._ssh:
            self._ssh.disconnect()

    def scans_collected(self) -> int:
        """Return number of scans collected.

        Returns:
            int: Number of eye scans collected
        """
        return self._scanner.scans_collected() if self._scanner else 0

    def run_eye_scan_loop(self, cfg: Config) -> int:
        """Run continuous eye scan loop.

        Args:
            cfg: Configuration with scan settings

        Returns:
            int: Number of successful scans completed
        """
        scan_count = 0
        while not shutdown_event.is_set():
            try:
                self._logger.info(f"Start scan iteration #{scan_count + 1}")
                if self.scan_interfaces(cfg.slx_scan_ports):
                    scan_count += 1
                    self._logger.info(f"Completed scan #{scan_count}")
                else:
                    self._logger.warning(f"Scan iteration #{scan_count + 1} failed")

                # Wait before next scan (check shutdown every second)
                if not shutdown_event.is_set():
                    self._logger.info(
                        f"Waiting {cfg.slx_scan_interval_sec} seconds before next scan..."
                    )
                    for _ in range(cfg.slx_scan_interval_sec):
                        if shutdown_event.is_set():
                            self._logger.info(LogMsg.SHUTDOWN_SIGNAL.value)
                            break
                        time.sleep(1)

            except Exception:
                self._logger.exception(LogMsg.MAIN_SCAN_ITERATION_FAILED.value)
                if not shutdown_event.is_set():
                    self._logger.info(LogMsg.MAIN_RETRY_WAIT.value)
                    time.sleep(5)

        return scan_count


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
        logger.debug(f"{LogMsg.CMD_EXECUTING.value}: '{cmd}'")
        result = self._ssh.exec_cmd(cmd)
        logger.debug(f"{LogMsg.CMD_RESULT.value}:\n{result.stdout}")
        return result.stdout, result.rcode

    def connect(self) -> bool:
        """Establish SSH connection and initialize software manager.

        Connects via jump host, tests connection with basic commands,
        and initializes software manager for package operations.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self._cfg.sut_connect_type == ConnectType.LOCAL:
                self._logger.info(LogMsg.MAIN_LOCAL_EXEC.value)
                self._ssh = LocalConnection(
                    host=self._cfg.sut_host, sudo_pass=self._cfg.sut_sudo_pass
                )
            else:
                self._logger.info(f"Connecting to host: {self._cfg.sut_host}")
                self._logger.debug(f"Using jump host: {self._cfg.jump_host}")
                self._ssh = _create_ssh_connection(self._cfg, HostType.SUT)

            if not self._ssh.connect():
                self._logger.error(LogMsg.SSH_CONN_FAILED.value)
                return False

            if self._cfg.sut_connect_type == ConnectType.LOCAL:
                self._logger.debug(LogMsg.MAIN_LOCAL_CONN_ESTABLISHED.value)
            else:
                self._logger.debug(LogMsg.MAIN_SSH_ESTABLISHED.value)
                # Shell not needed for system scanner - using execute_command instead
                self._logger.debug(LogMsg.MAIN_SHELL_SKIP.value)

            # Test connection with simple commands
            test_commands = ["whoami", "pwd"]
            self._logger.debug(f"Testing connection with commands: {test_commands}")

            for cmd in test_commands:
                stdout, rcode = self._exec_with_logging(cmd, self._logger)  # noqa: RUF059
                if rcode != 0:
                    result = self._ssh.exec_cmd(cmd)
                    self._logger.warning(f"Command '{cmd}' failed (rc={rcode}): {result.stderr}")

            self._logger.info(LogMsg.SSH_CONN_SUCCESS.value)
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception(LogMsg.MAIN_CONN_FAILED.value)
            return False

    def _ensure_software_manager(self) -> bool:
        """Ensure software manager is initialized.

        Returns:
            bool: True if initialized, False on error
        """
        if not self._software_manager:
            try:
                self._logger.debug(LogMsg.MAIN_SW_MGR_INIT.value)
                self._software_manager = SoftwareManager(self._ssh)
                self._logger.debug(LogMsg.SW_MGR_INIT.value)
            except Exception:
                self._logger.exception(LogMsg.SW_MGR_INIT_FAILED.value)
                return False
        return True

    def install_required_software(self) -> bool:
        """Install required software packages via software manager.

        Returns:
            bool: True if installation successful, False otherwise
        """
        if not self._ensure_software_manager():
            return False

        try:
            self._logger.info(LogMsg.MAIN_SW_INSTALL_START.value)
            self._logger.debug(f"Packages to install: {self._cfg.sut_required_software_packages}")
            result = self._software_manager.install_required_packages(
                self._cfg.sut_required_software_packages
            )
            self._logger.info(f"Software installation complete: {result}")
            return result  # noqa: TRY300
        except Exception:
            self._logger.exception(LogMsg.MAIN_SW_INSTALL_FAILED.value)
            return False

    def log_required_software_versions(self) -> bool:
        """Log versions of required software packages.

        Returns:
            bool: True if logging successful, False otherwise
        """
        if not self._ensure_software_manager():
            return False

        try:
            self._logger.info(LogMsg.SW_PKG_VERSION_CHECK.value)
            self._logger.debug(f"Packages to check: {self._cfg.sut_required_software_packages}")
            self._software_manager.log_required_package_versions(
                self._cfg.sut_required_software_packages
            )
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception(LogMsg.MAIN_SW_VERSION_FAILED.value)
            return False

    def log_system_info(self, logger: logging.Logger) -> None:
        """Log system information using available tools.

        Iterates through all available tools from ToolFactory,
        executes them, and logs their output.

        Args:
            logger: Logger instance for tool output
        """
        try:
            self._logger.info(LogMsg.SYS_INFO_LOG.value)
            available_tools = ToolFactory.get_available_tools()
            self._logger.debug(f"Available tools: {available_tools}")

            for tool_type in available_tools:
                self._logger.debug(f"Executing tool: {tool_type}")
                tool = ToolFactory.create_tool(
                    tool_type=tool_type,
                    ssh=self._ssh,
                    interfaces=self._cfg.sut_scan_interfaces,
                    logger=logger,
                )
                tool.execute()
                tool.log(logger)
                self._logger.debug(f"Tool {tool_type} completed")
        except Exception:
            self._logger.exception(LogMsg.SYS_INFO_FAILED.value)

    def run_scanners(self, cfg: Config) -> bool:
        """Start background worker threads for metrics collection.

        Creates workers per interface:
        - mlxlink: Network metrics (temp, voltage, power, BER)
        - mget_temp: NIC temperature
        - dmesg: Link flap detection

        All workers run in both local and remote modes.
        Use skip flags in show_parts to disable specific workers.

        Args:
            cfg: Configuration containing interfaces to scan

        Returns:
            bool: True if workers started successfully, False otherwise
        """
        try:
            self._logger.info(LogMsg.WORKER_START.value)
            self._logger.debug(f"Creating workers for interfaces: {cfg.sut_scan_interfaces}")
            self._logger.debug(f"Show parts config: {cfg.sut_show_parts}")

            # Determine which workers to create based on skip flags
            skip_mlxlink = ShowPartType.NO_MLXLINK in cfg.sut_show_parts
            skip_mlxlink_amber = ShowPartType.NO_MLXLINK_AMBER in cfg.sut_show_parts
            skip_mtemp = ShowPartType.NO_MTEMP in cfg.sut_show_parts
            skip_ethtool = ShowPartType.NO_ETHTOOL in cfg.sut_show_parts
            skip_dmesg = ShowPartType.NO_DMESG in cfg.sut_show_parts

            worker_count = 0
            for interface in cfg.sut_scan_interfaces:
                self._logger.debug(f"Setting up workers for interface: '{interface}'")
                pci_id = helper.get_pci_id(self._ssh, interface)
                self._logger.debug(f"PCI ID for '{interface}': '{pci_id}'")

                # Create workers unless explicitly skipped
                if not skip_mlxlink:
                    self._create_mlxlink_worker(pci_id)
                    worker_count += 1
                if not skip_mlxlink_amber:
                    self._create_mlxlink_amber_worker(pci_id)
                    worker_count += 1
                if not skip_mtemp:
                    self._create_mtemp_worker(pci_id)
                    worker_count += 1
                if not skip_ethtool:
                    self._create_ethtool_worker(interface)
                    worker_count += 1
                if not skip_dmesg:
                    self._create_dmesg_worker(interface)
                    worker_count += 1

            self._logger.info(f"Created {worker_count} worker(s)")
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception(LogMsg.WORKER_FAILED.value)
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
            "physical_grade",
            "height_eye",
            "phase_eye",
        ]

        worker_cfg = WorkerConfig()
        worker_cfg.command = f"mlxlink -d {pci_id} -e -m -c"
        worker_cfg.parser = MlxlinkParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = sut_mxlink_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_mlxlink_amber_worker(self, pci_id: str) -> None:
        """Create mlxlink amber worker for raw amber data collection.

        Args:
            pci_id: PCI device ID
        """
        worker_cfg = WorkerConfig()
        worker_cfg.pre_command = "rm -f /tmp/amber.csv"
        worker_cfg.command = (
            f"mlxlink -d {pci_id} --amber_collect /tmp/amber.csv && cat /tmp/amber.csv"
        )
        worker_cfg.parser = MlxlinkAmberParser()
        worker_cfg.logger = sut_mxlink_amber_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb
        worker_cfg.skip_header = True

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
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_low_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_ethtool_worker(self, interface: str) -> None:
        """Create ethtool worker for optical module metrics.

        Args:
            interface: Network interface name
        """
        attributes = [
            "laser_bias_current",
            "laser_output_power",
            "rx_power",
            "module_temperature",
            "module_voltage",
        ]

        worker_cfg = WorkerConfig()
        worker_cfg.command = f"ethtool -m {interface}"
        worker_cfg.parser = EthtoolModuleParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = sut_ethtool_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

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
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb
        worker_cfg.is_flap_logger = True

        self._add_worker_to_manager(worker_cfg)

    def _add_worker_to_manager(self, worker_cfg: WorkerConfig) -> None:
        self._logger.debug(f"Worker command: '{worker_cfg.command}'")
        shared_state = self._worker_manager.get_shared_flap_state()
        statistics = self._worker_manager.get_statistics()
        self._worker_manager.add(
            Worker(
                worker_cfg,
                self._cfg,
                self._ssh,
                shared_flap_state=shared_state,
                statistics=statistics,
            )
        )

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


def _create_ssh_connection(cfg: Config, host_type: HostType) -> SshConnection:
    """Create SSH connection with jump host.

    Args:
        cfg: Configuration object
        host_type: Host type (SLX or SUT) to determine which host to connect to

    Returns:
        SshConnection: Configured SshConnection object (not yet connected)
    """
    jump_host = Host(
        ip=cfg.jump_host,
        username=cfg.jump_user,
        password=cfg.jump_pass,
    )

    if host_type == HostType.SLX:
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
        cfg = load_cfg(_logger)

        _logger.debug(f"SLX host: {cfg.slx_host}, SUT host: {cfg.sut_host}")
    except Exception:
        _logger.exception(LogMsg.CONFIG_FAILED.value)
        return

    _logger.debug(LogMsg.SCANNER_INIT.value)

    slx_eye_scanner = SlxEyeScannerWrapper(cfg, slx_eye_logger)
    sut_system_scanner = SutSystemScanner(cfg, main_logger)

    try:
        _logger.info(LogMsg.SCANNER_INIT.value)
        if not sut_system_scanner.connect():
            _logger.error(LogMsg.SCANNER_CONN_FAILED.value)
            return

        # ---------------------------------------------------------------------------- #
        #                           Install required software                          #
        # ---------------------------------------------------------------------------- #

        skip_sys_info = ShowPartType.NO_SYS_INFO in cfg.sut_show_parts

        if not skip_sys_info:
            if not sut_system_scanner.install_required_software():
                _logger.warning(LogMsg.MAIN_SW_INSTALL_WARN.value)

            if not sut_system_scanner.log_required_software_versions():
                _logger.warning(LogMsg.MAIN_SW_VERSION_WARN.value)

            # ---------------------------------------------------------------------------- #
            #                            Log system information                            #
            # ---------------------------------------------------------------------------- #

            _logger.info(LogMsg.MAIN_SYS_INFO_START.value)
            sut_system_scanner.log_system_info(sut_system_info_logger)
        else:
            _logger.info(LogMsg.MAIN_SYS_INFO_SKIP.value)

        # ---------------------------------------------------------------------------- #
        #                         Start system scanning threads                        #
        # ---------------------------------------------------------------------------- #

        _logger.info(f"Scanning interfaces: {cfg.sut_scan_interfaces}")

        if not sut_system_scanner.run_scanners(cfg):
            _logger.warning(LogMsg.MAIN_SCAN_FAILED_START.value)

    except Exception:
        _logger.exception(LogMsg.MAIN_SCANNER_FAILED.value)

    # ---------------------------------------------------------------------------- #
    #                              Start eye scanning                              #
    # ---------------------------------------------------------------------------- #

    skip_eye_scan = ShowPartType.NO_EYE_SCAN in cfg.sut_show_parts

    if not skip_eye_scan:
        _logger.info(LogMsg.MAIN_EYE_SCAN_START.value)
        _logger.info(f"Scanning ports: {cfg.slx_scan_ports}")
        _logger.info(LogMsg.MAIN_EXIT_PROMPT.value)

        try:
            if not slx_eye_scanner.connect():
                _logger.error(LogMsg.MAIN_SLX_CONN_FAILED.value)
                return

            # Start eye scan loop in background thread
            scan_thread = threading.Thread(
                target=slx_eye_scanner.run_eye_scan_loop, args=(cfg,), daemon=True
            )
            scan_thread.start()
            scan_thread.join()
        except Exception:
            _logger.exception(LogMsg.MAIN_EXEC_FAILED.value)
    else:
        _logger.info("Eye scan skipped (NO_EYE_SCAN flag set)")
        # Keep main thread alive until Ctrl+C
        try:
            while not shutdown_event.is_set():
                time.sleep(1)
        except Exception:
            _logger.exception(LogMsg.MAIN_EXEC_FAILED.value)

    # Log shutdown signal
    _logger.info(LogMsg.SHUTDOWN_SIGNAL.value)

    # Pause logging and show worker shutdown countdown
    logging.disable(logging.CRITICAL)
    sys.stderr.write("\nWaiting for all threads to complete...\n")

    workers = sut_system_scanner.worker_manager.get_workers_in_pool()
    total_workers = len(workers)
    sys.stderr.write(f"\nStopping {total_workers} workers...\n")

    for idx, w in enumerate(workers, 1):
        w.close()
        sys.stderr.write(f"\rWorkers stopped: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n\nWaiting for workers to finish...\n")
    for idx, w in enumerate(workers, 1):
        w.join()
        sys.stderr.write(f"\rWorkers finished: {idx}/{total_workers}")
        sys.stderr.flush()

    sys.stderr.write("\n")
    logging.disable(logging.NOTSET)

    frame = PrettyFrame()
    shutdown_msg = frame.build("SHUTDOWN", ["Starting shutdown sequence..."])
    _logger.info(f"\n{shutdown_msg}")

    _logger.info(LogMsg.SHUTDOWN_EYE_SCANNER.value)
    slx_eye_scanner.disconnect()
    _logger.debug(LogMsg.MAIN_EYE_DISCONNECTED.value)

    _logger.info(LogMsg.WORKER_EXTRACT.value)
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
                        sample.begin.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] if sample.begin else ""
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

    _logger.info(LogMsg.WORKER_SHUTDOWN.value)

    _logger.debug(LogMsg.MAIN_SCANNER_DISCONNECT.value)
    sut_system_scanner.disconnect()

    stats_summary = sut_system_scanner.worker_manager.get_statistics_summary()
    _logger.info(f"\n{stats_summary}")

    # _logger.info("\n%s\n", "\n".join(headers_str))
    _logger.info(f"Total eye scans completed: {slx_eye_scanner.scans_collected()}")
    _logger.info(LogMsg.MAIN_SHUTDOWN_COMPLETE.value)
    _logger.info(LogMsg.MAIN_LOGS_SAVED.value)


if __name__ == "__main__":
    main()
