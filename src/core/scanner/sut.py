"""SUT scanner implementation."""

from datetime import UTC, datetime as dt
import logging
import threading
import time

from src.core.connect import LocalConnection, create_ssh_connection
from src.core.enums.connect import ConnectType, HostType, ShowPartType
from src.core.enums.messages import LogMsg
from src.core.parser import (
    SutDmesgFlapParser,
    SutEthtoolModuleParser,
    SutIpmitoolFanNameParser,
    SutIpmitoolFanParser,
    SutMlxlinkAmberParser,
    SutMlxlinkParser,
    SutTxErrorsParser,
)
from src.core.worker import WorkerConfig
from src.models.scanner import BaseScanner
from src.platform.software_manager import SoftwareManager
from src.platform.tools import helper
from src.platform.tools.tool_factory import ToolFactory


class SutScanner(BaseScanner):
    """SUT scanner for system monitoring and data collection."""

    def __init__(self, cfg, logger: logging.Logger, shutdown_event: threading.Event, loggers: dict):
        """Initialize SUT scanner.

        Args:
            cfg: Configuration object
            logger: Logger instance
            shutdown_event: Shutdown event
            loggers: Logger instances dict
        """
        super().__init__(cfg, logger, shutdown_event)
        self._sut_mxlink_logger = loggers["sut_mxlink"]
        self._sut_mxlink_amber_logger = loggers["sut_mxlink_amber"]
        self._sut_mtemp_logger = loggers["sut_mtemp"]
        self._sut_ethtool_logger = loggers["sut_ethtool"]
        self._sut_link_flap_logger = loggers["sut_link_flap"]
        self._sut_tx_errors_logger = loggers["sut_tx_errors"]
        self._sut_ipmitool_fan_logger = loggers["sut_ipmitool_fan"]
        self._system_info_logger = loggers["sut_system_info"]
        self._software_manager: SoftwareManager | None = None

    def _exec_with_logging(self, cmd: str, logger: logging.Logger) -> tuple[str, int]:
        """Execute command with logging.

        Args:
            cmd: Command to execute
            logger: Logger instance

        Returns:
            tuple[str, int]: Command output and return code
        """
        logger.debug(f"{LogMsg.CMD_EXECUTING.value}: '{cmd}'")
        result = self._ssh.exec_cmd(cmd)
        logger.debug(f"{LogMsg.CMD_RESULT.value}:\n\n{result.stdout}\n")
        return result.stdout, result.rcode

    def connect(self) -> bool:
        """Connect to SUT.

        Returns:
            bool: True if successful
        """
        try:
            if self._cfg.sut_connect_type == ConnectType.LOCAL:
                self._logger.info(LogMsg.MAIN_LOCAL_EXEC.value)
                self._ssh = LocalConnection(
                    host=self._cfg.sut_host, sudo_pass=self._cfg.sut_sudo_pass
                )
            else:
                self._logger.info(f"{LogMsg.SCANNER_SUT_CONN_HOST.value}: {self._cfg.sut_host}")
                self._logger.debug(f"{LogMsg.SCANNER_SUT_JUMP_HOST.value}: {self._cfg.jump_host}")
                self._ssh = create_ssh_connection(self._cfg, HostType.SUT)

            if not self._ssh.connect():
                self._logger.error(LogMsg.SSH_CONN_FAILED.value)
                return False

            if self._cfg.sut_connect_type == ConnectType.LOCAL:
                self._logger.debug(LogMsg.MAIN_LOCAL_CONN_ESTABLISHED.value)
            else:
                self._logger.debug(LogMsg.SSH_ESTABLISHED.value)
                self._logger.debug(LogMsg.SHELL_SKIP.value)

            test_commands = ["whoami", "pwd"]
            self._logger.debug(f"{LogMsg.SCANNER_SUT_TEST_CONN.value}: {test_commands}")

            for cmd in test_commands:
                stdout, rcode = self._exec_with_logging(cmd, self._logger)  # noqa: RUF059
                if rcode != 0:
                    result = self._ssh.exec_cmd(cmd)
                    self._logger.warning(
                        f"{LogMsg.SCANNER_SUT_CMD_FAILED.value} '{cmd}' (rc={rcode}): {result.stderr}"
                    )

            self._logger.info(LogMsg.SSH_CONN_SUCCESS.value)
        except Exception:
            self._logger.exception(LogMsg.MAIN_CONN_FAILED.value)
            return False
        else:
            return True

    def _ensure_software_manager(self) -> bool:
        """Ensure software manager is initialized.

        Returns:
            bool: True if initialized
        """
        if not self._software_manager:
            try:
                self._logger.debug(LogMsg.MAIN_SW_MGR_INIT.value)
                self._software_manager = SoftwareManager(self._ssh)
                self._logger.debug(LogMsg.MAIN_SW_MGR_INIT.value)
            except Exception:
                self._logger.exception(LogMsg.SW_MGR_INIT_FAILED.value)
                return False
        return True

    def install_required_software(self) -> bool:
        """Install required software packages.

        Returns:
            bool: True if successful
        """
        if not self._ensure_software_manager():
            return False

        try:
            self._logger.info(LogMsg.MAIN_SW_INSTALL_START.value)
            self._logger.debug(
                f"{LogMsg.SCANNER_SUT_PACKAGES_INSTALL.value}: {self._cfg.sut_required_software_packages}"
            )
            result = self._software_manager.install_required_packages(
                self._cfg.sut_required_software_packages
            )
            self._logger.info(f"{LogMsg.SCANNER_SUT_SW_COMPLETE.value}: {result}")
        except Exception:
            self._logger.exception(LogMsg.MAIN_SW_INSTALL_FAILED.value)
            return False
        else:
            return result

    def log_required_software_versions(self) -> bool:
        """Log versions of required software packages.

        Returns:
            bool: True if successful
        """
        if not self._ensure_software_manager():
            return False

        try:
            self._logger.info(LogMsg.SW_PKG_VERSION_CHECK.value)
            self._logger.debug(
                f"{LogMsg.SCANNER_SUT_PACKAGES_CHECK.value}: {self._cfg.sut_required_software_packages}"
            )
            self._software_manager.log_required_package_versions(
                self._cfg.sut_required_software_packages
            )
        except Exception:
            self._logger.exception(LogMsg.MAIN_SW_VERSION_FAILED.value)
            return False
        else:
            return True

    def log_system_info(self, logger: logging.Logger | None = None) -> None:
        """Log system information.

        Args:
            logger: Optional logger, defaults to system_info_logger
        """
        log = logger or self._system_info_logger
        try:
            self._logger.info(LogMsg.SYS_INFO_LOG.value)
            available_tools = ToolFactory.get_available_tools()
            self._logger.debug(f"{LogMsg.SCANNER_SUT_TOOLS_AVAILABLE.value}: {available_tools}")

            for tool_type in available_tools:
                self._logger.debug(f"{LogMsg.SCANNER_SUT_TOOL_EXEC.value}: {tool_type}")
                tool = ToolFactory.create_tool(
                    tool_type=tool_type,
                    ssh=self._ssh,
                    interfaces=self._cfg.sut_scan_interfaces,
                    logger=log,
                )
                tool.execute()
                tool.log(log)
                self._logger.debug(f"{LogMsg.SCANNER_SUT_TOOL_COMPLETE.value}: {tool_type}")
        except Exception:
            self._logger.exception(LogMsg.SYS_INFO_FAILED.value)

    def _reload_drivers(self) -> bool:
        """Reload mlx5 network drivers.

        Returns:
            bool: True if successful
        """
        try:
            self._logger.info("Reloading mlx5 drivers...")
            interfaces = self._cfg.sut_scan_interfaces

            # Take down links
            for iface in interfaces:
                result = self._ssh.exec_cmd(f"ip link set {iface} down", 30)
                if result.rcode != 0:
                    self._logger.error(f"Failed to bring down {iface}: {result.stderr}")
                    return False
            self._logger.debug(f"Links down: {interfaces}")

            # Remove drivers
            result = self._ssh.exec_cmd("modprobe -r mlx5_ib", 120)
            if result.rcode != 0:
                self._logger.warning(f"Failed to remove mlx5_ib: {result.stderr}")
            result = self._ssh.exec_cmd("modprobe -r mlx5_core", 120)
            if result.rcode != 0:
                self._logger.error(f"Failed to remove mlx5_core: {result.stderr}")
                return False
            self._logger.debug("Drivers removed")

            # Load drivers
            result = self._ssh.exec_cmd("modprobe mlx5_core", 120)
            if result.rcode != 0:
                self._logger.error(f"Failed to load mlx5_core: {result.stderr}")
                return False
            result = self._ssh.exec_cmd("modprobe mlx5_ib", 120)
            if result.rcode != 0:
                self._logger.warning(f"Failed to load mlx5_ib: {result.stderr}")
            self._logger.debug("Drivers loaded")

            # Wait for driver initialization
            time.sleep(2)

            # Bring up links
            for iface in interfaces:
                result = self._ssh.exec_cmd(f"ip link set {iface} up", 30)
                if result.rcode != 0:
                    self._logger.error(f"Failed to bring up {iface}: {result.stderr}")
                    return False
            self._logger.info(f"Driver reload complete: {interfaces}")
        except Exception:
            self._logger.exception("Driver reload failed")
            return False
        else:
            return True

    def run(self) -> None:
        """Run SUT scanning."""
        if not self.connect():
            self._logger.error(LogMsg.SCANNER_CONN_FAILED.value)
            return

        skip_sys_info = ShowPartType.NO_SYS_INFO in self._cfg.sut_show_parts

        if not skip_sys_info:
            if not self.install_required_software():
                self._logger.warning(LogMsg.MAIN_SW_INSTALL_WARN.value)

            if not self.log_required_software_versions():
                self._logger.warning(LogMsg.MAIN_SW_VERSION_WARN.value)

            self._logger.info(LogMsg.SYS_INFO_START.value)
            self.log_system_info(self._system_info_logger)
        else:
            self._logger.info(LogMsg.SYS_INFO_SKIP.value)

        if self._cfg.sut_reload_driver and not self._reload_drivers():
            return

        self._logger.info(
            f"{LogMsg.SCANNER_SUT_SCAN_INTERFACES.value}: {self._cfg.sut_scan_interfaces}"
        )
        if not self._start_workers():
            self._logger.warning(LogMsg.MAIN_SCAN_FAILED_START.value)

    def _start_workers(self) -> bool:
        """Start worker threads.

        Returns:
            bool: True if successful
        """
        try:
            self._logger.info(LogMsg.WORKER_START.value)
            self._logger.debug(
                f"{LogMsg.SCANNER_SUT_WORKERS_FOR.value}: {self._cfg.sut_scan_interfaces}"
            )
            self._logger.debug(f"{LogMsg.SCANNER_SUT_SHOW_PARTS.value}: {self._cfg.sut_show_parts}")

            skip_mlxlink = ShowPartType.NO_MLXLINK in self._cfg.sut_show_parts
            skip_mlxlink_amber = ShowPartType.NO_MLXLINK_AMBER in self._cfg.sut_show_parts
            skip_mtemp = ShowPartType.NO_MTEMP in self._cfg.sut_show_parts
            skip_ethtool = ShowPartType.NO_ETHTOOL in self._cfg.sut_show_parts
            skip_dmesg = ShowPartType.NO_DMESG in self._cfg.sut_show_parts
            skip_tx_errors = ShowPartType.NO_TX_ERRORS in self._cfg.sut_show_parts
            skip_fan = ShowPartType.NO_FAN in self._cfg.sut_show_parts

            # Create fan worker once (not per interface)
            if not skip_fan:
                self._create_ipmitool_fan_worker()
                worker_count = 1
            else:
                worker_count = 0

            for interface in self._cfg.sut_scan_interfaces:
                self._logger.debug(f"{LogMsg.SCANNER_SUT_SETUP_INTERFACE.value}: '{interface}'")
                pci_id = helper.get_pci_id(self._ssh, interface)
                self._logger.debug(f"{LogMsg.SCANNER_SUT_PCI_ID.value} '{interface}': '{pci_id}'")

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
                if not skip_tx_errors:
                    self._create_tx_errors_worker(interface)
                    worker_count += 1

            self._logger.info(
                f"{LogMsg.SCANNER_WORKERS_CREATED.value}: {worker_count} (SUT monitoring)"
            )
        except Exception:
            self._logger.exception(LogMsg.WORKER_FAILED.value)
            return False
        else:
            return True

    def _create_mlxlink_worker(self, pci_id: str) -> None:
        """Create mlxlink worker.

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
        worker_cfg.parser = SutMlxlinkParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = self._sut_mxlink_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_mlxlink_amber_worker(self, pci_id: str) -> None:
        """Create mlxlink amber worker.

        Args:
            pci_id: PCI device ID
        """
        worker_cfg = WorkerConfig()
        worker_cfg.pre_command = "rm -f /tmp/amber.csv"
        worker_cfg.command = (
            f"mlxlink -d {pci_id} --amber_collect /tmp/amber.csv && cat /tmp/amber.csv"
        )
        worker_cfg.parser = SutMlxlinkAmberParser()
        worker_cfg.logger = self._sut_mxlink_amber_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb
        worker_cfg.skip_header = True

        self._add_worker_to_manager(worker_cfg)

    def _create_mtemp_worker(self, pci_id: str) -> None:
        """Create temperature worker.

        Args:
            pci_id: PCI device ID
        """
        worker_cfg = WorkerConfig()
        worker_cfg.command = f"mget_temp -d {pci_id}"
        worker_cfg.parser = None
        worker_cfg.logger = self._sut_mtemp_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_low_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_ethtool_worker(self, interface: str) -> None:
        """Create ethtool worker.

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
        worker_cfg.parser = SutEthtoolModuleParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = self._sut_ethtool_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_dmesg_worker(self, interface: str) -> None:
        """Create dmesg worker.

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
        worker_cfg.parser = SutDmesgFlapParser(dt.now(UTC))
        worker_cfg.attributes = attributes
        worker_cfg.logger = self._sut_link_flap_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_high_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb
        worker_cfg.is_flap_logger = True

        self._add_worker_to_manager(worker_cfg)

    def _create_tx_errors_worker(self, interface: str) -> None:
        """Create tx_errors worker.

        Args:
            interface: Network interface name
        """
        attributes = ["tx_errors"]

        worker_cfg = WorkerConfig()
        worker_cfg.command = f"cat /sys/class/net/{interface}/statistics/tx_errors"
        worker_cfg.parser = SutTxErrorsParser()
        worker_cfg.attributes = attributes
        worker_cfg.logger = self._sut_tx_errors_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_tx_errors_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)

    def _create_ipmitool_fan_worker(self) -> None:
        """Create ipmitool fan worker."""
        worker_cfg = WorkerConfig()
        worker_cfg.command = "ipmitool sensor | grep Fan"
        worker_cfg.attribute_command = "ipmitool sensor | grep Fan"
        worker_cfg.attribute_parser = SutIpmitoolFanNameParser()
        worker_cfg.parser = SutIpmitoolFanParser()
        worker_cfg.logger = self._sut_ipmitool_fan_logger
        worker_cfg.scan_interval_ms = self._cfg.sut_scan_interval_low_res_ms
        worker_cfg.max_log_size_kb = self._cfg.sut_scan_max_log_size_kb

        self._add_worker_to_manager(worker_cfg)
