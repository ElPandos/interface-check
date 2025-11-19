"""SLX Eye Scanner for automated eye scan execution on SLX switches."""

from dataclasses import dataclass
import logging
import re
import time

from src.core.connect import SshConnection
from src.core.enums.messages import LogMsg


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

    def __init__(self, ssh: SshConnection, logger: logging.Logger):
        """Initialize SLX eye scanner.

        Args:
            ssh: SSH connection to SLX switch
            logger: Logger instance for this scanner
        """
        self._ssh = ssh
        self._logger = logger
        self._results: list[EyeScanResult] = []
        self._interface_cache: dict[str, tuple[str, str]] = {}

    def _exec_with_logging(self, cmd: str, cmd_description: str = "") -> str:
        """Execute shell command with automatic pre/post logging.

        Args:
            cmd: Command to execute
            cmd_description: Optional description for logging (defaults to cmd)

        Returns:
            str: Command output
        """
        log_cmd = cmd_description if cmd_description else cmd
        self._logger.debug(f"{LogMsg.CMD_EXECUTING.value}: '{log_cmd}'")
        result = self._ssh.exec_shell_command(cmd)
        self._logger.debug(f"{LogMsg.CMD_RESULT.value}:\n{result}")
        return result

    def setup_shell(self, sudo_pass: str) -> bool:
        """Setup SLX shell environment.

        Opens shell, enters Linux shell mode, and elevates to root user.

        Args:
            sudo_pass: Root password for SLX switch

        Returns:
            bool: True if setup successful, False otherwise
        """
        try:
            if not self._ssh.open_shell():
                self._logger.error(LogMsg.SHELL_OPEN_FAILED.value)
                return False
            self._logger.debug(LogMsg.MAIN_SHELL_OPENED.value)

            # Enter Linux shell
            self._exec_with_logging("start-shell")

            # Switch to root user
            self._exec_with_logging("su root")

            # Provide password
            self._logger.debug(LogMsg.MAIN_SUDO_PASSWORD.value)
            result = self._exec_with_logging(sudo_pass, "password")
            self._logger.debug(f"{LogMsg.MAIN_PASSWORD_AUTH_RESULT.value}: {result}")

            self._logger.info(f"{LogMsg.SSH_CONN_SUCCESS.value} (in Linux shell)")
            return True  # noqa: TRY300
        except Exception:
            self._logger.exception("Failed to setup SLX shell environment")
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
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return None

        cmd = f"cmsh -e 'hsl ifm show localdb' | grep {interface}"

        try:
            result = self._exec_with_logging(cmd, f"cmsh for interface '{interface}'")

            pattern = rf"{re.escape(interface)}\s+0x[0-9a-fA-F]+\s+\d+\s+(\d+)"
            self._logger.debug(f"{LogMsg.PATTERN_SEARCH.value}: '{pattern}'")
            match = re.search(pattern, result)

            if match:
                port_id = match.group(1)
                self._logger.info(
                    f"{LogMsg.PORT_ID_FOUND.value} '{port_id}' for interface: '{interface}'"
                )
                return port_id
            self._logger.warning(f"{LogMsg.PORT_ID_NOT_FOUND.value} '{interface}'")
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
            self._logger.info(f"{LogMsg.FBR_ENTERING.value} {purpose}")
        else:
            self._logger.info(LogMsg.FBR_ENTERING.value)
        self._logger.debug(f"{LogMsg.CMD_EXECUTING.value}: 'fbr-CLI'")
        self._ssh.exec_shell_command("fbr-CLI")
        time.sleep(0.5)

        welcome_msg = self._ssh.exec_shell_command("")
        self._logger.debug(f"{LogMsg.CMD_RESULT.value}:\n{welcome_msg}")
        self._logger.info(LogMsg.MAIN_FBR_ENTERED.value)

    def _exit_fbr_cli(self) -> None:
        """Exit fbr-CLI back to Linux shell using Ctrl+C."""
        self._logger.info(LogMsg.MAIN_FBR_EXIT_CTRL_C.value)
        self._exec_with_logging("\x03", "Ctrl+C")
        time.sleep(0.3)
        self._logger.info(LogMsg.FBR_EXITED.value)

    def get_interface_name(self, port_id: str) -> str | None:
        """Find interface name by port ID in fbr-CLI.

        Args:
            port_id: Port identifier from cmsh

        Returns:
            str | None: Interface name (e.g., 'xe1') if found, None otherwise
        """
        if not self._ssh:
            self._logger.error(LogMsg.SSH_NO_CONN.value)
            return None

        try:
            self._enter_fbr_cli(f"to find interface for port {port_id}")
            ps_result = self._exec_with_logging("ps")
            self._exit_fbr_cli()

            pattern = rf"(\w+)\(\s*{re.escape(port_id)}\s*\)"
            self._logger.debug(f"{LogMsg.PATTERN_SEARCH.value}: '{pattern}'")
            match = re.search(pattern, ps_result)

            if match:
                interface_name = match.group(1)
                self._logger.info(
                    f"{LogMsg.INTERFACE_FOUND.value} '{interface_name}' for port: '{port_id}'"
                )
                return interface_name
            self._logger.warning(f"{LogMsg.INTERFACE_NOT_FOUND.value}: '{port_id}'")
            return None  # noqa: TRY300
        except Exception:
            self._logger.exception(f"Failed to get interface name for port: '{port_id}'")
            return None

    def enable_interface(self, port_name: str) -> None:
        """Enable interface via fbr-CLI port command.

        Args:
            port_name: Interface name (e.g., 'xe1')
        """
        self._execute_toggle(f"port {port_name} enable=true")

    def disable_interface(self, port_name: str) -> None:
        """Disable interface via fbr-CLI port command.

        Args:
            port_name: Interface name (e.g., 'xe1')
        """
        self._execute_toggle(f"port {port_name} enable=false")

    def _execute_toggle(self, cmd: str, wait_sec: int = 5) -> None:
        """Execute port toggle command in fbr-CLI.

        Args:
            cmd: Port toggle command (e.g., 'port xe1 enable=true')
            wait_sec: Seconds to wait after toggle
        """
        if not self._ssh:
            self._logger.error(f"{LogMsg.SSH_NO_CONN.value} for toggle")
            return

        try:
            self._enter_fbr_cli("for toggle")
            self._logger.debug(f"{LogMsg.TOGGLE_EXECUTING.value}: '{cmd}'")
            self._exec_with_logging(cmd)
            self._exit_fbr_cli()
            self._logger.debug(f"{LogMsg.TOGGLE_WAITING.value}: {wait_sec} seconds...")
            time.sleep(wait_sec)
        except Exception:
            self._logger.exception(f"{LogMsg.TOGGLE_FAILED.value} '{cmd}'")

    def run_eye_scan(
        self,
        interface: str,
        port_id: str,
        toggle_enabled: bool = False,
        toggle_wait_sec: int = 5,
        scan_wait_sec: int = 20,
    ) -> None:
        """Execute eye scan with optional interface toggle.

        Args:
            interface: Interface name (e.g., 'xe1')
            port_id: Port identifier for logging
            toggle_enabled: Whether to toggle port before scan
            toggle_wait_sec: Seconds to wait after toggle
            scan_wait_sec: Seconds to wait for scan completion
        """
        if not self._ssh:
            self._logger.error(f"{LogMsg.SSH_NO_CONN.value} for eye scan")
            return

        try:
            self._logger.info(f"{LogMsg.EYE_SCAN_START.value} '{interface}' (Port: '{port_id}')")

            if toggle_enabled:
                self._logger.info(LogMsg.TOGGLE_ENABLED.value)
                self.disable_interface(interface)
                time.sleep(toggle_wait_sec)
                self.enable_interface(interface)

            self._enter_fbr_cli("for eye scan")

            self._logger.info(LogMsg.MAIN_BUFFER_CLEARING.value)
            self._ssh.clear_shell()
            self._logger.info(LogMsg.MAIN_BUFFER_CLEARED.value)

            cmd = f"phy diag {interface} eyescan"
            self._logger.info(f"{LogMsg.CMD_EXECUTING.value} eye scan: '{cmd}'")
            self._ssh.exec_shell_command(cmd + "\n", until_prompt=False)

            self._logger.info(f"Waiting {scan_wait_sec}s for eye scan")
            time.sleep(scan_wait_sec)

            result = self._ssh.exec_shell_command("\n")

            self._results.append(EyeScanResult(interface, port_id, result))
            self._logger.info(
                f"{LogMsg.EYE_SCAN_COMPLETE.value}: '{interface}' (Port: '{port_id}')"
            )
            self._logger.info("=" * 39)
            self._logger.info("\n%s", self._results[-1].result)
            self._logger.info("=" * 39)

            self._exit_fbr_cli()

        except Exception:
            self._logger.exception(f"{LogMsg.EYE_SCAN_FAILED.value} for '{interface}'")

    def _lookup_interface_mapping(self, interface: str) -> tuple[str, str] | None:
        """Lookup port ID and interface name for given interface.

        Args:
            interface: Interface name to lookup

        Returns:
            tuple[str, str] | None: Tuple of (port_id, interface_name) if found, None otherwise
        """
        self._logger.info(f"{LogMsg.INTERFACE_LOOKUP.value} for '{interface}'")

        port_id = self.get_port_id(interface)
        if not port_id:
            self._logger.error(
                f"{LogMsg.PORT_ID_NOT_FOUND.value} '{interface}', {LogMsg.SCAN_SKIPPING.value}"
            )
            return None

        interface_name = self.get_interface_name(port_id)
        if not interface_name:
            self._logger.error(
                f"{LogMsg.INTERFACE_NOT_FOUND.value} '{port_id}', {LogMsg.SCAN_SKIPPING.value}"
            )
            return None

        return (port_id, interface_name)

    def scan_interfaces(
        self,
        interfaces: list[str],
        toggle_enabled: bool = False,
        toggle_wait_sec: int = 5,
        scan_wait_sec: int = 20,
    ) -> bool:
        """Complete eye scan workflow for multiple interfaces.

        Args:
            interfaces: List of interface names to scan
            toggle_enabled: Whether to toggle ports before scanning
            toggle_wait_sec: Seconds to wait after toggle
            scan_wait_sec: Seconds to wait for scan completion

        Returns:
            bool: True if at least one scan succeeded, False otherwise
        """
        if not interfaces:
            self._logger.warning(LogMsg.SCAN_NO_INTERFACES.value)
            return True

        self._logger.info(f"{LogMsg.SCAN_START.value}: {len(interfaces)} interfaces: {interfaces}")
        success_count = 0

        for interface in interfaces:
            self._logger.debug(f"{LogMsg.SCAN_PROCESSING.value}: '{interface}'")
            try:
                if interface in self._interface_cache:
                    port_id, interface_name = self._interface_cache[interface]
                    self._logger.debug(
                        f"{LogMsg.CACHE_HIT.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
                    )
                else:
                    mapping = self._lookup_interface_mapping(interface)
                    if not mapping:
                        continue

                    port_id, interface_name = mapping
                    self._interface_cache[interface] = (port_id, interface_name)
                    self._logger.info(
                        f"{LogMsg.CACHE_MISS.value}: '{interface}' -> '{interface_name}' (Port: '{port_id}')"
                    )

                self.run_eye_scan(
                    interface_name, port_id, toggle_enabled, toggle_wait_sec, scan_wait_sec
                )
                success_count += 1

            except Exception:
                self._logger.exception(f"Failed to scan interface '{interface}'")
                continue

        self._logger.info(f"{LogMsg.SCAN_COMPLETE.value}: {success_count}/{len(interfaces)}")
        return success_count > 0

    def scans_collected(self) -> int:
        """Return number of scans collected.

        Returns:
            int: Number of eye scans collected
        """
        return len(self._results)

    def get_results(self) -> list[EyeScanResult]:
        """Get all collected eye scan results.

        Returns:
            list[EyeScanResult]: List of eye scan results
        """
        return self._results
