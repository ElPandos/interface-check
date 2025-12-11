"""SLX scanner implementation."""

from dataclasses import dataclass
import logging
import re
import threading
import time

from src.core.connect import create_ssh_connection
from src.core.enums.connect import HostType, PortState, ShowPartType
from src.core.enums.messages import LogMsg
from src.core.log.rotation import check_and_rotate_log
from src.models.scanner import BaseScanner


@dataclass
class ScanResult:
    """Scan result data."""

    interface: str
    port_id: str
    result: str


class SlxScanner(BaseScanner):
    """SLX scanner for eye scan and DSC diagnostics."""

    def __init__(
        self,
        cfg,
        logger: logging.Logger,
        shutdown_event: threading.Event,
        loggers: dict,
        shared_flap_state: dict | None = None,
    ):
        """Initialize SLX scanner.

        Args:
            cfg: Configuration object
            logger: Logger instance
            shutdown_event: Shutdown event
            loggers: Logger instances dict
            shared_flap_state: Shared flap state dict from SUT scanner
        """
        super().__init__(cfg, logger, shutdown_event)
        self._eye_logger = loggers["slx_eye"]
        self._dsc_logger = loggers["slx_dsc"]
        self._results: list[ScanResult] = []
        self._interface_cache: dict[str, tuple[str, str]] = {}
        self._scan_type: str = ""  # "eye" or "dsc"
        self._shared_flap_state = shared_flap_state or {"flaps_detected": False}
        self._has_rotated_since_flap: dict[str, bool] = {}  # Track per logger
        self._log_rotation_count: dict[str, int] = {}  # Track per logger
        self._toggle_count = 0  # Track number of toggles performed

    def _get_logger(self) -> logging.Logger:
        """Get appropriate logger based on scan type.

        Returns:
            logging.Logger: Eye or DSC logger
        """
        return self._eye_logger if self._scan_type == "eye" else self._dsc_logger

    def _exec_with_logging(self, cmd: str, cmd_description: str = "") -> str:
        """Execute shell command with logging.

        Args:
            cmd: Command to execute
            cmd_description: Optional description

        Returns:
            str: Command output
        """
        logger = self._get_logger()
        log_cmd = cmd_description if cmd_description else cmd
        logger.debug(f"{LogMsg.CMD_EXECUTING.value}: '{log_cmd}'")
        result = self._ssh.exec_shell_cmd(cmd, logger=logger)
        logger.debug(f"{LogMsg.CMD_RESULT.value}:{result}")
        return result

    def connect(self) -> bool:
        """Connect to SLX and setup environment.

        Returns:
            bool: True if successful
        """
        try:
            self._logger.info(f"{LogMsg.SCANNER_SLX_CONN_HOST.value}: {self._cfg.slx_host}")
            self._logger.debug(f"{LogMsg.SCANNER_SUT_JUMP_HOST.value}: {self._cfg.jump_host}")
            self._ssh = create_ssh_connection(self._cfg, HostType.SLX)

            if not self._ssh.connect():
                self._logger.error(LogMsg.SSH_CONN_FAILED.value)
                return False
            self._logger.debug(LogMsg.SSH_ESTABLISHED.value)

            if not self._ssh.open_shell():
                self._logger.error(LogMsg.SHELL_OPEN_FAILED.value)
                return False
            self._logger.debug(LogMsg.SHELL_OPENED.value)

            self._exec_with_logging("start-shell")
            self._exec_with_logging("su root")
            self._logger.debug(LogMsg.MAIN_SUDO_PASSWORD.value)
            result = self._exec_with_logging(self._cfg.slx_sudo_pass, "password")
            self._logger.debug(f"{LogMsg.MAIN_PASSWORD_AUTH_RESULT.value}: {result}")
            self._logger.info(f"{LogMsg.SSH_CONN_SUCCESS.value} (in Linux shell)")
        except Exception:
            self._logger.exception(LogMsg.MAIN_CONN_FAILED.value)
            return False
        else:
            return True

    def _get_port_id(self, interface: str) -> str | None:
        """Extract port ID from cmsh output.

        Args:
            interface: Interface name

        Returns:
            str | None: Port ID if found
        """
        logger = self._get_logger()
        if not self._ssh:
            logger.error(LogMsg.SSH_NO_CONN.value)
            return None

        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"

        try:
            result = self._exec_with_logging(cmd, f"cmsh for interface '{interface}'")
            pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
            logger.debug(f"{LogMsg.PATTERN_SEARCH.value}: '{pattern}'")
            match = re.search(pattern, result)

            if match:
                port_id = match.group(1)
                logger.info(
                    f"{LogMsg.PORT_ID_FOUND.value} '{port_id}' for interface: '{interface}'"
                )
                return port_id
            logger.warning(f"{LogMsg.PORT_ID_NOT_FOUND.value} '{interface}'")
        except Exception:
            logger.exception(f"Failed to get port ID for '{interface}'")
            return None
        else:
            return port_id

    def _enter_fbr_cli(self, purpose: str = "") -> None:
        """Enter fbr-CLI.

        Args:
            purpose: Optional description
        """
        logger = self._get_logger()
        if purpose:
            logger.info(f"{LogMsg.FBR_ENTERING.value} {purpose}")
        else:
            logger.info(LogMsg.FBR_ENTERING.value)
        logger.debug(f"{LogMsg.CMD_EXECUTING.value}: 'fbr-CLI'")
        self._ssh.exec_shell_cmd("fbr-CLI")
        time.sleep(0.5)
        welcome_msg = self._ssh.exec_shell_cmd("")
        logger.debug(f"{LogMsg.CMD_RESULT.value}:\n\n{welcome_msg}\n")
        logger.info(LogMsg.FBR_ENTERED.value)

    def _exit_fbr_cli(self) -> None:
        """Exit fbr-CLI."""
        logger = self._get_logger()
        logger.info(LogMsg.FBR_EXIT_CTRL_C.value)
        self._exec_with_logging("\x03", "Ctrl+C")
        time.sleep(0.3)
        logger.info(LogMsg.FBR_EXITED.value)

    def _get_interface_name(self, port_id: str) -> str | None:
        """Find interface name by port ID.

        Args:
            port_id: Port identifier

        Returns:
            str | None: Interface name if found
        """
        logger = self._get_logger()
        if not self._ssh:
            logger.error(LogMsg.SSH_NO_CONN.value)
            return None

        try:
            self._enter_fbr_cli(f"to find interface for port: {port_id}")
            ps_result = self._ssh.exec_shell_cmd("ps")
            logger.debug(f"{LogMsg.CMD_RESULT.value}:\n\n{ps_result}\n")
            self._exit_fbr_cli()

            pattern = rf"(\w+)\(\s*{re.escape(port_id)}\s*\)"
            logger.debug(f"{LogMsg.PATTERN_SEARCH.value}: '{pattern}'")
            match = re.search(pattern, ps_result)

            if match:
                interface_name = match.group(1)
                logger.info(
                    f"{LogMsg.INTERFACE_FOUND.value} '{interface_name}' for port: '{port_id}'"
                )
                return interface_name
            logger.warning(f"{LogMsg.INTERFACE_NOT_FOUND.value}: '{port_id}'")
        except Exception:
            logger.exception(f"Failed to get interface name for port: '{port_id}'")
            return None
        else:
            return interface_name

    def _toggle_interface(self, port_name: str, state: PortState, wait_sec: int = 5) -> None:
        """Toggle interface state.

        Args:
            port_name: Interface name
            state: Port state (PortState.ON or PortState.OFF)
            wait_sec: Seconds to wait after toggle
        """
        logger = self._get_logger()
        if not self._ssh:
            logger.error(f"{LogMsg.SSH_NO_CONN.value} for toggle")
            return

        try:
            logger.info(f"Toggling port '{port_name}': {state.display_name}")
            self._enter_fbr_cli("for toggle")
            cmd = f"port {port_name} enable={state.value}"
            self._exec_with_logging(cmd)
            self._exit_fbr_cli()
            logger.debug(f"{LogMsg.TOGGLE_WAITING.value}: {wait_sec} seconds...")
            time.sleep(wait_sec)
        except Exception:
            logger.exception(f"{LogMsg.TOGGLE_FAILED.value} for '{port_name}'")

    def _run_eye_scan(
        self,
        interface: str,
        port_id: str,
        toggle_limit: int = -1,
        toggle_wait_sec: int = 5,
        scan_wait_sec: int = 20,
    ) -> None:
        """Execute eye scan.

        Args:
            interface: Interface name
            port_id: Port identifier
            toggle_limit: -1=disabled, 0=unlimited, >0=max toggles
            toggle_wait_sec: Seconds to wait after toggle
            scan_wait_sec: Seconds to wait for scan
        """
        if not self._ssh:
            self._eye_logger.error(f"{LogMsg.SSH_NO_CONN.value} for eye scan")
            return

        try:
            self._eye_logger.info(
                f"{LogMsg.EYE_SCAN_START.value} '{interface}' (Port: '{port_id}')"
            )

            # Check if toggling should be performed
            should_toggle = toggle_limit == 0 or (
                toggle_limit > 0 and self._toggle_count < toggle_limit
            )
            if should_toggle:
                self._eye_logger.info(
                    f"Toggle enabled (count={self._toggle_count}, limit={toggle_limit})"
                )
                self._toggle_interface(interface, PortState.OFF, toggle_wait_sec)
                self._toggle_interface(interface, PortState.ON, toggle_wait_sec)
                self._toggle_count += 1
            elif toggle_limit > 0:
                self._eye_logger.info(f"Toggle limit reached ({self._toggle_count}/{toggle_limit})")

            self._enter_fbr_cli("for eye scan")
            self._eye_logger.info(LogMsg.BUFFER_CLEARING.value)
            self._ssh.clear_shell()
            self._eye_logger.info(LogMsg.BUFFER_CLEARED.value)

            cmd = f"phy diag {interface} eyescan"
            self._eye_logger.info(f"{LogMsg.CMD_EXECUTING.value} eye scan: '{cmd}'")
            self._ssh.exec_shell_cmd(cmd + "\n", until_prompt=False)
            self._eye_logger.info(f"Waiting {scan_wait_sec} seconds for eye scan")
            time.sleep(scan_wait_sec)
            result = self._ssh.exec_shell_cmd("\n")

            if self._cfg.worker_collect:
                self._results.append(ScanResult(interface, port_id, result))

            self._eye_logger.info(
                f"{LogMsg.EYE_SCAN_COMPLETE.value}: '{interface}' (Port: '{port_id}')"
            )
            self._eye_logger.info("=" * 39)
            self._eye_logger.info("\n%s", result)
            self._eye_logger.info("=" * 39)
            self._check_and_rotate_log(self._eye_logger, self._cfg.sut_scan_max_log_size_kb)
            self._exit_fbr_cli()
        except Exception:
            self._eye_logger.exception(f"{LogMsg.EYE_SCAN_FAILED.value} for '{interface}'")

    def _get_cached_or_lookup(self, interface: str) -> tuple[str, str] | None:
        """Get cached mapping or lookup interface.

        Args:
            interface: Interface name

        Returns:
            tuple[str, str] | None: (port_id, interface_name) if found
        """
        logger = self._get_logger()
        if interface in self._interface_cache:
            port_id, interface_name = self._interface_cache[interface]
            logger.debug(
                f"{LogMsg.CACHE_HIT.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
            )
            return (port_id, interface_name)

        logger.info(f"{LogMsg.INTERFACE_LOOKUP.value} for '{interface}'")
        port_id = self._get_port_id(interface)
        if not port_id:
            logger.error(
                f"{LogMsg.PORT_ID_NOT_FOUND.value} '{interface}', {LogMsg.SCAN_SKIPPING.value}"
            )
            return None

        interface_name = self._get_interface_name(port_id)
        if not interface_name:
            logger.error(
                f"{LogMsg.INTERFACE_NOT_FOUND.value} '{port_id}', {LogMsg.SCAN_SKIPPING.value}"
            )
            return None

        self._interface_cache[interface] = (port_id, interface_name)
        logger.info(
            f"{LogMsg.CACHE_MISS.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
        )
        return (port_id, interface_name)

    def _scan_eye_interfaces(self, interfaces: list[str]) -> bool:
        """Complete eye scan workflow.

        Args:
            interfaces: List of interface names

        Returns:
            bool: True if at least one scan succeeded
        """
        if not interfaces:
            self._eye_logger.warning(LogMsg.SCAN_NO_INTERFACES.value)
            return True

        self._eye_logger.info(
            f"{LogMsg.SCAN_START.value}: {len(interfaces)} interfaces: {interfaces}"
        )
        success_count = 0

        for interface in interfaces:
            self._eye_logger.debug(f"{LogMsg.SCAN_PROCESSING.value}: '{interface}'")
            try:
                mapping = self._get_cached_or_lookup(interface)
                if not mapping:
                    continue
                port_id, interface_name = mapping
                self._run_eye_scan(
                    interface_name,
                    port_id,
                    self._cfg.slx_port_toggle_limit,
                    self._cfg.slx_port_toggle_wait_sec,
                    self._cfg.slx_port_eyescan_wait_sec,
                )
                success_count += 1
            except Exception:
                self._eye_logger.exception(f"Failed to scan interface '{interface}'")
                continue

        self._eye_logger.info(f"{LogMsg.SCAN_COMPLETE.value}: {success_count}/{len(interfaces)}")
        return success_count > 0

    def scans_collected(self) -> int:
        """Return number of scans collected.

        Returns:
            int: Number of scans
        """
        return len(self._results)

    def _scan_dsc_interfaces(self, interfaces: list[str]) -> bool:
        """Run DSC diagnostics.

        Args:
            interfaces: List of interface names

        Returns:
            bool: True if at least one scan succeeded
        """
        if not interfaces:
            self._dsc_logger.warning("No interfaces for DSC scan")
            return True

        success_count = 0
        for interface in interfaces:
            try:
                mapping = self._get_cached_or_lookup(interface)
                if not mapping:
                    continue
                _, port_id = mapping

                cmd = f"phy diag {port_id} dsc"
                self._dsc_logger.debug(f"Executing DSC: '{cmd}'")
                result = self._ssh.exec_shell_cmd(cmd, logger=self._dsc_logger)

                # Parse DSC output - extract data lines only
                output_lines = []
                in_data = False
                for line in result.split("\n"):
                    if line.startswith(("CORE RST_ST", "LN (CDRxN")):
                        in_data = True
                    elif "****" in line or "Legend of Entries" in line:
                        in_data = False
                    if in_data and (
                        line.strip()[:1].isdigit() or line.startswith((" 0", "CORE", "LN"))
                    ):
                        output_lines.append(line)

                parsed_result = "\n".join(output_lines) if output_lines else result

                if self._cfg.worker_collect:
                    self._results.append(ScanResult(interface, port_id, parsed_result))

                self._dsc_logger.info(f"DSC scan complete: '{interface}' (Port: '{port_id}')")
                self._dsc_logger.info("=" * 39)
                self._dsc_logger.info("\n%s", parsed_result)
                self._dsc_logger.info("=" * 39)
                self._check_and_rotate_log(self._dsc_logger, self._cfg.sut_scan_max_log_size_kb)
                success_count += 1
            except Exception:
                self._dsc_logger.exception(f"Failed DSC scan for '{interface}'")
                continue

        return success_count > 0

    def run(self) -> None:
        """Run SLX scanning."""
        skip_eye = ShowPartType.NO_SLX_EYE in self._cfg.sut_show_parts
        skip_dsc = ShowPartType.NO_SLX_DSC in self._cfg.sut_show_parts

        if skip_eye and skip_dsc:
            self._logger.info(LogMsg.SCANNER_SLX_SKIP.value)
            return

        # Set scan type based on what's enabled
        self._scan_type = "dsc" if not skip_dsc else "eye"

        if not self.connect():
            self._logger.error(LogMsg.MAIN_SLX_CONN_FAILED.value)
            return

        self._logger.info(f"{LogMsg.SCANNER_SLX_PORTS.value}: {self._cfg.slx_scan_ports}")
        if not self._start_workers():
            self._logger.warning(LogMsg.SCANNER_START_FAILED.value)

    def _start_workers(self) -> bool:
        """Start SLX workers.

        Returns:
            bool: True if successful
        """
        skip_eye = ShowPartType.NO_SLX_EYE in self._cfg.sut_show_parts
        skip_dsc = ShowPartType.NO_SLX_DSC in self._cfg.sut_show_parts

        try:
            self._logger.info(LogMsg.WORKER_START.value)
            worker_count = 0

            if not skip_dsc:
                self._create_dsc_worker()
                worker_count += 1
            if not skip_eye:
                self._create_eye_worker()
                worker_count += 1

            scan_types = []
            if not skip_dsc:
                scan_types.append("DSC")
            if not skip_eye:
                scan_types.append("Eye")
            types_str = "+".join(scan_types) if scan_types else "None"
            self._logger.info(
                f"{LogMsg.SCANNER_WORKERS_CREATED.value}: {worker_count} (SLX {types_str})"
            )
        except Exception:
            self._logger.exception(LogMsg.SCANNER_START_FAILED.value)
            return False
        else:
            return True

    def _create_eye_worker(self) -> None:
        """Create eye scan worker thread."""
        self._scan_type = "eye"
        self._logger.info(LogMsg.MAIN_EYE_SCAN_START.value)
        self._logger.info(LogMsg.MAIN_EXIT_PROMPT.value)
        scan_thread = threading.Thread(target=self._run_eye_scan_loop, daemon=True)
        scan_thread.start()

    def _create_dsc_worker(self) -> None:
        """Create DSC scan worker thread."""
        self._scan_type = "dsc"
        self._logger.info(LogMsg.SCANNER_DSC_START.value)
        dsc_thread = threading.Thread(target=self._run_dsc_scan_loop, daemon=True)
        dsc_thread.start()

    def _check_and_rotate_log(self, logger: logging.Logger, max_size_kb: int) -> None:
        """Check log file size and rotate if needed.

        Args:
            logger: Logger to check
            max_size_kb: Maximum log size in KB
        """
        check_and_rotate_log(
            logger,
            max_size_kb,
            self._shared_flap_state,
            self._has_rotated_since_flap,
            self._log_rotation_count,
            keep_header=False,  # SLX logs are not CSV format
            timeout_sec=self._cfg.log_rotation_timeout_sec,
        )

    def _interruptible_sleep(self, seconds: int, logger: logging.Logger | None = None) -> None:
        """Sleep with shutdown event checking.

        Args:
            seconds: Seconds to sleep
            logger: Optional logger for shutdown message
        """
        for _ in range(seconds):
            if self._shutdown_event.is_set():
                if logger:
                    logger.info(LogMsg.SHUTDOWN_SIGNAL.value)
                break
            time.sleep(1)

    def _run_dsc_scan_loop(self) -> int:
        """Run continuous DSC scan loop.

        Returns:
            int: Number of scans completed
        """
        self._scan_type = "dsc"
        scan_count = 0

        # Pre-lookup all interfaces before entering fbr-CLI
        self._dsc_logger.info(
            f"Pre-looking up {len(self._cfg.slx_scan_ports)} interfaces before fbr-CLI"
        )
        for interface in self._cfg.slx_scan_ports:
            if interface not in self._interface_cache:
                result = self._get_cached_or_lookup(interface)
                if result:
                    self._dsc_logger.debug(f"Pre-lookup success: '{interface}'")
                else:
                    self._dsc_logger.warning(f"Pre-lookup failed: '{interface}'")

        self._enter_fbr_cli("for DSC")

        while not self._shutdown_event.is_set():
            try:
                self._dsc_logger.info(f"{LogMsg.SCANNER_DSC_ITER_START.value} #{scan_count + 1}")
                if self._scan_dsc_interfaces(self._cfg.slx_scan_ports):
                    scan_count += 1
                    self._dsc_logger.info(f"{LogMsg.SCANNER_DSC_ITER_COMPLETE.value} #{scan_count}")
                else:
                    self._dsc_logger.warning(
                        f"{LogMsg.SCANNER_DSC_ITER_FAILED.value} #{scan_count + 1}"
                    )

                if not self._shutdown_event.is_set():
                    self._interruptible_sleep(self._cfg.sut_scan_interval_high_res_ms // 1000 or 1)
            except Exception:
                self._dsc_logger.exception(LogMsg.SCANNER_DSC_ITER_FAILED.value)
                if not self._shutdown_event.is_set():
                    time.sleep(5)

        self._exit_fbr_cli()
        return scan_count

    def _run_eye_scan_loop(self) -> int:
        """Run continuous eye scan loop.

        Returns:
            int: Number of scans completed
        """
        self._scan_type = "eye"
        scan_count = 0

        while not self._shutdown_event.is_set():
            try:
                self._eye_logger.info(f"{LogMsg.SCANNER_EYE_ITER_START.value} #{scan_count + 1}")
                if self._scan_eye_interfaces(self._cfg.slx_scan_ports):
                    scan_count += 1
                    self._eye_logger.info(f"{LogMsg.SCANNER_EYE_ITER_COMPLETE.value} #{scan_count}")
                else:
                    self._eye_logger.warning(
                        f"{LogMsg.SCANNER_EYE_ITER_FAILED.value} #{scan_count + 1}"
                    )

                if not self._shutdown_event.is_set():
                    self._eye_logger.info(
                        f"{LogMsg.SCANNER_EYE_WAIT.value}: {self._cfg.slx_scan_interval_sec}"
                    )
                    self._interruptible_sleep(self._cfg.slx_scan_interval_sec, self._eye_logger)
            except Exception:
                self._eye_logger.exception(LogMsg.SCANNER_EYE_ITER_FAILED.value)
                if not self._shutdown_event.is_set():
                    self._eye_logger.info(LogMsg.MAIN_RETRY_WAIT.value)
                    time.sleep(5)

        return scan_count
