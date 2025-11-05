#!/usr/bin/env python3
"""Optimized SLX eye scan automation."""

from dataclasses import dataclass
from datetime import datetime as dt
import json
import logging
from pathlib import Path
import re
import signal
import sys
import threading
import time

from src.core.connect import SshConnection
from src.core.parser import MlxlinkParser
from src.core.worker import Worker, WorkerCommand, WorkManager
from src.models.config import Host
from src.platform.enums.log import LogName
from src.platform.software_manager import SoftwareManager
from src.platform.tools import helper
from src.platform.tools.tool_factory import ToolFactory

# Event for graceful shutdown
shutdown_event = threading.Event()


def signal_handler(_signum, _frame) -> None:
    # Logger not available yet, use stderr
    sys.stderr.write("Ctrl+C pressed. Shutting down gracefully...\n")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)

# Setup robust logging with separate loggers
log_time_stamp = f"{dt.now(tz=dt.now().astimezone().tzinfo).strftime('%Y%m%d_%H%M%S')}"
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Log files
main_log = log_dir / f"{log_time_stamp}_main.log"
sut_system_info_log = log_dir / f"{log_time_stamp}_sut_system_info.log"
sut_value_scanner_log = log_dir / f"{log_time_stamp}_sut_value_scan.log"
slx_eye_scanner_log = log_dir / f"{log_time_stamp}_slx_eye_scan.log"


###########################
#
log_level = logging.INFO
#
###########################

# Log formatter
log_format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configure root logger
logging.basicConfig(
    level=log_level,
    format=log_format_string,
    handlers=[
        logging.FileHandler(main_log),
        logging.StreamHandler(),
    ],
)

# Main logger
main_logger = logging.getLogger(LogName.MAIN.value)

# Create specialized loggers
sut_system_info_logger = logging.getLogger(LogName.SUT_SYSTEM_INFO.value)
sut_value_scanner_logger = logging.getLogger(LogName.SUT_VALUE_SCANNER.value)
slx_eye_scanner_logger = logging.getLogger(LogName.SLX_EYE_SCANNER.value)

# Add file handlers for specialized loggers
sut_system_info_handler = logging.FileHandler(sut_system_info_log)
slx_eye_scanner_handler = logging.FileHandler(slx_eye_scanner_log)
sut_value_scanner_handler = logging.FileHandler(sut_value_scanner_log)

for handler in [slx_eye_scanner_handler, sut_system_info_handler, sut_value_scanner_handler]:
    handler.setFormatter(logging.Formatter(log_format_string))
    handler.setLevel(log_level)

slx_eye_scanner_logger.addHandler(slx_eye_scanner_handler)
sut_system_info_logger.addHandler(sut_system_info_handler)
sut_value_scanner_logger.addHandler(sut_value_scanner_handler)

# Prevent duplicate logs in root logger
slx_eye_scanner_logger.propagate = False
sut_system_info_logger.propagate = False
sut_value_scanner_logger.propagate = False


@dataclass(frozen=True)
class Config:
    """Connection configuration."""

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
        """Create Config from nested JSON structure."""
        jump = data["jump"]
        slx = data["slx"]
        sut = data["sut"]

        return cls(
            jump_host=jump["host"],
            jump_user=jump["user"],
            jump_pass=jump["pass"],
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


def load_config() -> Config:
    """Load configuration from JSON file."""
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        config_file = Path(sys.executable).parent / "main_eye_config.json"
    else:
        # Running as script
        config_file = Path(__file__).parent / "main_eye_config.json"
    try:
        with config_file.open() as f:
            data = json.load(f)
        return Config.from_dict(data)
    except FileNotFoundError:
        main_logger.exception(f"Config file not found: {config_file}")
        main_logger.exception("Make sure config.json is in the same directory as the executable")
        raise
    except json.JSONDecodeError:
        main_logger.exception("Invalid JSON in config file")
        raise


@dataclass
class EyeScanResult:
    """Eye scan result data."""

    interface: str
    port_id: str
    result: str


class SlxEyeScanner:
    """SLX eye scan automation."""

    def __init__(self, config: Config):
        self._config = config
        self._results: list[EyeScanResult] = []
        self._interface_cache: dict[str, tuple[str, str]] = {}
        self._ssh_connection: SshConnection | None = None
        self.logger = slx_eye_scanner_logger

    def connect(self) -> bool:
        """Establish SSH connection and setup environment."""
        try:
            self.logger.info(f"Connecting to SLX host: {self._config.slx_host}")
            host = Host(
                ip=self._config.jump_host,
                username=self._config.jump_user,
                password=self._config.jump_pass,
            )
            self._ssh_connection = SshConnection(
                host=self._config.slx_host,
                username=self._config.slx_user,
                password=self._config.slx_pass,
                jump_hosts=[host],
            )

            if not self._ssh_connection.connect():
                self.logger.error("Failed to establish SSH connection")
                return False

            if not self._ssh_connection.open_shell():
                self.logger.error("Failed to open shell")
                return False

            # Setup shell environment on SLX OS
            commands = ["start-shell", "su root", self._config.slx_sudo_pass]

            for cmd in commands:
                self.logger.debug(f"Executing setup command: {cmd}")
                result = self._ssh_connection.execute_shell_command(cmd)
                self.logger.debug(f"Command result: {result}")

            self.logger.info("SLX connection established successfully")
        except Exception:
            self.logger.exception("Connection failed")
            return False
        else:
            return True

    def get_port_id(self, interface: str) -> str | None:
        """Extract port ID from cmsh output."""
        if not self._ssh_connection:
            self.logger.error("No SSH connection available")
            return None

        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"
        self.logger.debug(f"Getting port ID for {interface}: {cmd}")

        try:
            result = self._ssh_connection.execute_shell_command(cmd)
            self.logger.debug(f"Port ID command result: {result}")

            pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
            match = re.search(pattern, result)

            if match:
                port_id = match.group(1)
                self.logger.info(f"Found port ID {port_id} for interface {interface}")
                return port_id
            self.logger.warning(f"No port ID found for interface {interface}")
        except Exception:
            self.logger.exception(f"Failed to get port ID for {interface}")
            return None
        else:
            return None

    def get_interface_name(self, port_id: str) -> str | None:
        """Find interface name by port ID in fbr-CLI."""
        if not self._ssh_connection:
            self.logger.error("No SSH connection available")
            return None

        try:
            self.logger.debug(f"Entering fbr-CLI to find interface for port {port_id}")
            self._ssh_connection.execute_shell_command("fbr-CLI")
            ps_result = self._ssh_connection.execute_shell_command("ps")
            self.logger.debug(f"fbr-CLI ps result: {ps_result}")

            pattern = rf"(\w+)\(\s*{re.escape(port_id)}\)"
            match = re.search(pattern, ps_result)

            if match:
                interface_name = match.group(1)
                self.logger.info(f"Found interface name {interface_name} for port {port_id}")
                return interface_name
            self.logger.warning(f"No interface name found for port {port_id}")
        except Exception:
            self.logger.exception(f"Failed to get interface name for port {port_id}")
            return None
        else:
            return None

    def enable_interface(self, interface_name: str) -> None:
        """Enable interface."""
        command = f"port {interface_name} enable=true"
        self._execute_toggle(command)

    def disable_interface(self, interface: str) -> None:
        """Disable interface."""
        command = f"port {interface} enable=false"
        self._execute_toggle(command)

    def _execute_toggle(self, command: str) -> None:
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for toggle")
            return

        try:
            self.logger.info(f"Toggling interface: {command}")
            result = self._ssh_connection.execute_shell_command(command)
            self.logger.debug(f"Toggle command result: {result}")

            self.logger.info(
                f"Waiting {self._config.slx_port_toggle_wait} seconds for interface toggle to take effect..."
            )
            time.sleep(self._config.slx_port_toggle_wait)

        except Exception:
            self.logger.exception(f"Failed to execute toggle command '{command}'")

    def run_eye_scan(self, interface: str, port_id: str) -> None:
        """Execute eye scan with interface toggle sequence."""
        if not self._ssh_connection:
            self.logger.error("No SSH connection available for eye scan")
            return

        try:
            self.logger.info(f"Starting eye scan for interface {interface} (Port: {port_id})")

            if self._config.slx_port_toggle_enabled:
                self.logger.info("Port toggling enabled, disabling then enabling interface")
                self.disable_interface(interface)
                self.enable_interface(interface)

            # Run eye scan
            cmd = f"phy diag {interface} eyescan"
            self.logger.info(f"Executing eye scan command: {cmd}")

            # Send command and wait
            self._ssh_connection.execute_shell_command(cmd + "\n", until_prompt=False)
            self.logger.info(
                f"Waiting {self._config.slx_port_eyescan_wait} seconds for eye scan to complete..."
            )
            time.sleep(self._config.slx_port_eyescan_wait)

            # Get results
            result = self._ssh_connection.execute_shell_command("\n")

            self._results.append(EyeScanResult(interface, port_id, result))
            self.logger.info(f"Eye scan completed for: {interface} (Port: {port_id})")
            self.logger.info("=======================================")
            self.logger.info(self._results[-1].result)
            self.logger.info("=======================================")

        except Exception:
            self.logger.exception(f"Failed to run eye scan for {interface}")

    def scan_interfaces(self, interfaces: list[str]) -> bool:
        """Complete eye scan workflow for interfaces."""
        if not interfaces:
            self.logger.warning("No interfaces provided for scanning")
            return True

        self.logger.info(f"Starting scan for {len(interfaces)} interfaces: {interfaces}")
        success_count = 0

        for interface in interfaces:
            try:
                # Check cache first
                if interface in self._interface_cache:
                    port_id, interface_name = self._interface_cache[interface]
                    self.logger.debug(
                        f"Using cached mapping: {interface} -> {interface_name} (Port {port_id})"
                    )
                else:
                    # First time lookup
                    self.logger.info(f"Looking up interface mapping for {interface}")
                    port_id = self.get_port_id(interface)
                    if not port_id:
                        self.logger.error(f"No port ID found for {interface}, skipping")
                        continue

                    interface_name = self.get_interface_name(port_id)
                    if not interface_name:
                        self.logger.error(f"No interface found for port {port_id}, skipping")
                        continue

                    # Cache the mapping
                    self._interface_cache[interface] = (port_id, interface_name)
                    self.logger.info(
                        f"Cached mapping: {interface} -> {interface_name} (Port {port_id})"
                    )

                self.run_eye_scan(interface_name, port_id)
                success_count += 1

            except Exception:
                self.logger.exception(f"Failed to scan interface {interface}")
                continue

        self.logger.info(
            f"Completed scanning {success_count}/{len(interfaces)} interfaces successfully"
        )
        return success_count > 0

    def disconnect(self) -> None:
        """Clean up connection."""
        if self._ssh_connection:
            self._ssh_connection.disconnect()


@dataclass
class TempResult:
    """Temp result data."""

    interface: str
    value: float
    unit: str


class SutSystemScanner:
    """SUT system scan automation."""

    def __init__(self, config: Config):
        self._config = config
        self._temps: list[TempResult] = []
        self._ssh_connection: SshConnection | None = None
        self._software_manager: SoftwareManager | None = None

        self._worker_manager = WorkManager()

    def connect(self) -> bool:
        """Establish SSH connection and setup environment."""
        try:
            sut_system_info_logger.info(f"Connecting to SUT host: {self._config.sut_host}")
            host = Host(
                ip=self._config.jump_host,
                username=self._config.jump_user,
                password=self._config.jump_pass,
            )
            self._ssh_connection = SshConnection(
                host=self._config.sut_host,
                username=self._config.sut_user,
                password=self._config.sut_pass,
                jump_hosts=[host],
            )

            if not self._ssh_connection.connect():
                sut_system_info_logger.error("Failed to establish SSH connection")
                return False

            # Shell not needed for SUT system scanner - using execute_command instead
            sut_system_info_logger.debug("Skipping shell opening for SUT connection")

            # Test connection with simple commands
            test_commands = ["whoami", "pwd"]

            for cmd in test_commands:
                sut_system_info_logger.debug(f"Testing connection with command: {cmd}")
                result = self._ssh_connection.execute_command(cmd)
                if result.return_code == 0:
                    sut_system_info_logger.debug(f"Command '{cmd}' result: {result.stdout.strip()}")
                else:
                    sut_system_info_logger.warning(f"Command '{cmd}' failed: {result.stderr}")

            self._software_manager = SoftwareManager(self._ssh_connection)
            sut_system_info_logger.info("SUT connection established successfully")
        except Exception:
            sut_system_info_logger.exception("SUT connection failed")
            return False
        else:
            return True

    def install_required_software(self) -> bool:
        """Install required software packages."""
        if not self._software_manager:
            sut_system_info_logger.error("Software manager not initialized")
            return False

        try:
            sut_system_info_logger.info("Installing required software packages")
            result = self._software_manager.install_required_packages(
                self._config.sut_required_software_packages, self._config.sut_sudo_pass
            )
            sut_system_info_logger.info(f"Software installation completed: {result}")
        except Exception:
            sut_system_info_logger.exception("Failed to install required software")
            return False
        else:
            return result

    def log_required_software_versions(self) -> bool:
        """Log versions of required software packages."""
        if not self._software_manager:
            sut_system_info_logger.error("Software manager not initialized")
            return False
        try:
            sut_system_info_logger.info("Logging required software versions")
            self._software_manager.log_required_package_versions(
                self._config.sut_required_software_packages
            )
        except Exception:
            sut_system_info_logger.exception("Failed to log software versions")
            return False
        else:
            return True

    def log_system_info(self) -> None:
        """Log system information."""
        try:
            sut_system_info_logger.info("Logging system information")
            for tool_type in ToolFactory.get_available_tools():
                tool = ToolFactory.create_tool(
                    tool_type=tool_type,
                    ssh_connection=self._ssh_connection,
                    interfaces=self._config.sut_scan_interfaces,  # Use None for system info, not interface list
                )
                tool.execute()
                tool.log()
        except Exception:
            sut_system_info_logger.exception("Failed to log system info")

    def run_scanner(self, config: Config) -> bool:
        """Start scanning thread."""
        try:
            sut_value_scanner_logger.info("Starting scanning")

            for interface in config.sut_scan_interfaces:
                # Mlxlink values
                worker_command_1 = WorkerCommand()
                worker_command_1.command = (
                    f"sudo mlxlink -d {helper.get_pci_id(self._ssh_connection, interface)} -e -m -c"
                )
                worker_command_1.parser = MlxlinkParser
                self._worker_manager.add(
                    Worker(worker_command_1, self._config, self._ssh_connection)
                )

                # MFT temp value
                worker_command_2 = WorkerCommand()
                worker_command_2.command = (
                    f"sudo mget_temp -d {helper.get_pci_id(self._ssh_connection, interface)}"
                )
                worker_command_2.parser = None
                self._worker_manager.add(
                    Worker(worker_command_2, self._config, self._ssh_connection)
                )

        except Exception:
            sut_value_scanner_logger.exception("Failed to start scanning")
            return False
        else:
            return True

    @property
    def worker_manager(self) -> WorkManager:
        return self._worker_manager

    def disconnect(self) -> None:
        """Clean up connection."""
        if self._ssh_connection:
            self._ssh_connection.disconnect()


def main():  # noqa: PLR0912, PLR0915
    """Main execution with continuous scanning loop."""
    try:
        config = load_config()
        main_logger.info("Configuration loaded successfully")
    except Exception:
        main_logger.exception("Failed to load configuration")
        return

    slx_eye_scanner = SlxEyeScanner(config)
    sut_system_scanner = SutSystemScanner(config)

    try:
        main_logger.info("Starting SUT system scanner initialization")
        if not sut_system_scanner.connect():
            main_logger.error("Failed to connect to SUT system")
            return

        main_logger.info(f"Starting system information scan. Logs saved to: {sut_system_info_log}")

        # ---------------------------------------------------------------------------- #
        #                           Install required software                          #
        # ---------------------------------------------------------------------------- #

        # if not sut_system_scanner.install_required_software():
        #     main_logger.warning("Software installation failed, continuing anyway")

        # if not sut_system_scanner.log_required_software_versions():
        #     main_logger.warning("Failed to log software versions")

        # ---------------------------------------------------------------------------- #
        #                                Log system info                               #
        # ---------------------------------------------------------------------------- #

        # sut_system_scanner.log_system_info()

        # ---------------------------------------------------------------------------- #
        #                          Start temp scanning thread                          #
        # ---------------------------------------------------------------------------- #

        main_logger.info(f"Starting system interface scan. Logs saved to: {sut_value_scanner_log}")

        sut_value_scanner_logger.info(f"Scanning interfaces: {config.sut_scan_interfaces}")

        if not sut_system_scanner.run_scanner(config):
            main_logger.warning("Temperature scanning failed to start")

    except Exception:
        main_logger.exception("SUT system scanner failed")

    # ---------------------------------------------------------------------------- #
    #                              Start eye scanning                              #
    # ---------------------------------------------------------------------------- #

    main_logger.info(f"Starting eye scan automation. Logs saved to: {slx_eye_scanner_log}")
    main_logger.info(f"Scanning ports: {config.slx_scan_ports}")
    main_logger.info("Press Ctrl+C to stop the program")

    try:
        if not slx_eye_scanner.connect():
            main_logger.error("Failed to connect to SLX eye scanner")
            return

        scan_count = 0
        while not shutdown_event.is_set():
            try:
                main_logger.info(f"Starting scan iteration #{scan_count + 1}")
                # Scan ports in config
                if slx_eye_scanner.scan_interfaces(config.slx_scan_ports):
                    scan_count += 1
                    main_logger.info(f"Completed scan #{scan_count}")
                else:
                    main_logger.warning(f"Scan iteration #{scan_count + 1} failed")

                # Wait before next scan (if still running)
                if not shutdown_event.is_set():
                    main_logger.info(
                        f"Waiting {config.slx_scan_interval} seconds before next scan..."
                    )
                    for _ in range(config.slx_scan_interval):
                        if shutdown_event.is_set():
                            break
                        time.sleep(1)

            except Exception:
                main_logger.exception("Scan iteration failed")
                if not shutdown_event.is_set():
                    main_logger.info("Waiting 5 seconds before retry...")
                    time.sleep(5)  # Brief pause before retry

    except Exception:
        main_logger.exception("Main execution failed")
    finally:
        main_logger.info("Shutting down eye scanner...")
        slx_eye_scanner.disconnect()

        main_logger.info("Extracting SUT system value scanner samples...")
        workers = sut_system_scanner.worker_manager.get_workers_in_pool()
        for w in workers:
            w.extract_all_samples()

        matrix_str = []

        # Build matrix with smallest list determining rows
        all_samples = [w.get_extracted_samples() for w in workers]
        min_rows = min(len(samples) for samples in all_samples) if all_samples else 0

        if min_rows > 0:
            matrix_str = []

            # Title row
            headers = [
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
                "m_temp [NIC]",
            ]
            headers_str = ",".join(headers)
            matrix_str.append(headers_str)
            sut_value_scanner_logger.info(headers_str)
            # Data rows
            for i in range(min_rows):
                row = []
                for worker_idx, samples in enumerate(all_samples):
                    sample = samples[i]
                    if worker_idx == 0:  # First worker - MlxlinkDevice attributes
                        row.extend(
                            [
                                str(sample.snapshot.temperature.value)
                                if hasattr(sample.snapshot, "temperature")
                                and sample.snapshot.temperature is not None
                                else "",
                                str(sample.snapshot.voltage.value)
                                if hasattr(sample.snapshot, "voltage")
                                and sample.snapshot.voltage is not None
                                else "",
                                str(sample.snapshot.bias_current.value)
                                if hasattr(sample.snapshot, "bias_current")
                                and sample.snapshot.bias_current is not None
                                else "",
                                str(sample.snapshot.rx_power.value)
                                if hasattr(sample.snapshot, "rx_power")
                                and sample.snapshot.rx_power is not None
                                else "",
                                str(sample.snapshot.tx_power.value)
                                if hasattr(sample.snapshot, "tx_power")
                                and sample.snapshot.tx_power is not None
                                else "",
                                str(sample.snapshot.time_since_last_clear.value)
                                if hasattr(sample.snapshot, "time_since_last_clear")
                                and sample.snapshot.time_since_last_clear is not None
                                else "",
                                str(sample.snapshot.effective_physical_errors.value)
                                if hasattr(sample.snapshot, "effective_physical_errors")
                                and sample.snapshot.effective_physical_errors is not None
                                else "",
                                str(sample.snapshot.effective_physical_ber.value)
                                if hasattr(sample.snapshot, "effective_physical_ber")
                                and sample.snapshot.effective_physical_ber is not None
                                else "",
                                str(sample.snapshot.raw_physical_errors_per_lane.value)
                                if hasattr(sample.snapshot, "raw_physical_errors_per_lane")
                                and sample.snapshot.raw_physical_errors_per_lane is not None
                                else "",
                                str(sample.snapshot.raw_physical_ber.value)
                                if hasattr(sample.snapshot, "raw_physical_ber")
                                and sample.snapshot.raw_physical_ber is not None
                                else "",
                            ]
                        )
                    else:  # Second worker - m_temp [NIC]
                        row.append(str(sample.snapshot) if hasattr(sample, "snapshot") else "")
                matrix_str.append(",".join(row))

            sut_value_scanner_logger.info("\n%s\n", "\n".join(matrix_str))

        main_logger.info("Shutting down system value scanner...")
        sut_system_scanner.worker_manager.stop_all()

        sut_system_scanner.disconnect()

    main_logger.info(
        f"Programs stopped. Total eye scans completed: {len(slx_eye_scanner._results)}"  # noqa: SLF001
    )
    main_logger.info("Logs saved to:")
    main_logger.info(f"  Main: {main_log}")
    main_logger.info(f"  SUT system info: {sut_system_info_log}")
    main_logger.info(f"  SUT value scan: {sut_value_scanner_log}")
    main_logger.info(f"  SLX eye xcan: {slx_eye_scanner_log}")

    return


if __name__ == "__main__":
    main()
