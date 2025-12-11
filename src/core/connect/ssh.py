"""SSH connection management."""

import logging
import re
import threading
import time
from typing import Any, ClassVar

import paramiko
from pydantic import SecretStr

from src.core.connect.local import _log_exec_time
from src.core.enums.connect import HostType
from src.core.enums.messages import LogMsg
from src.core.parser import SutTimeParser
from src.core.result import CmdResult
from src.interfaces.component import IConnection
from src.models.config import Host
from src.platform.enums.log import LogName


def create_ssh_connection(cfg, host_type: HostType) -> "SshConnection":
    """Create SSH connection with jump host.

    Args:
        cfg: Configuration object
        host_type: Target host type (SLX or SUT)

    Returns:
        SshConnection: Configured SSH connection
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
    return SshConnection(
        host=cfg.sut_host,
        username=cfg.sut_user,
        password=cfg.sut_pass,
        jump_hosts=[jump_host],
        sudo_pass=cfg.sut_sudo_pass,
    )


class SshConnection(IConnection):
    """SSH connection with jump host and keepalive support.

    Manages SSH connections with multi-hop support through jump hosts.
    Includes automatic keepalive and shell session management.
    """

    __slots__ = (
        "_exec_lock",
        "_host",
        "_jump_clients",
        "_jump_hosts",
        "_keepalive_interval",
        "_keepalive_thread",
        "_password",
        "_prompt_pattern",
        "_shell",
        "_ssh_client",
        "_stop_keepalive",
        "_username",
    )

    _SSH_DEFAULTS: ClassVar[dict[str, Any]] = {
        "look_for_keys": False,
        "allow_agent": False,
        "timeout": 30,
    }

    _PROMPT_PATTERN: ClassVar[bytes] = (
        rb"SLX#\s*$|\[.*@.*\][$#]\s*$|.*[$#]\s*$|Password:\s*$|password for.*:\s*$|FBR\.\d+>\s*$|.*@.*:.*[$#]\s*$|Shell>\s*$|.*>\s*$"
    )

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        username: str,
        password: str,
        jump_hosts: list[Host] | None = None,
        keepalive_interval: int = 30,
        sudo_pass="",
    ):
        """Initialize SSH connection.

        Args:
            host: Target host IP address
            username: SSH username
            password: SSH password
            jump_hosts: Optional list of jump hosts
            keepalive_interval: Keepalive interval in seconds
            sudo_pass: Optional sudo password
        """
        # Connection parameters
        self._host = host
        self._username = username
        self._password = password
        self._jump_hosts = jump_hosts or []
        self._keepalive_interval = keepalive_interval
        self._sudo_pass = sudo_pass

        # SSH clients
        self._ssh_client = None
        self._jump_clients = []

        # Keepalive management
        self._keepalive_thread = None
        self._stop_keepalive = threading.Event()

        # Shell session
        self._shell = None
        self._prompt_pattern = re.compile(self._PROMPT_PATTERN, re.MULTILINE)

        # Thread safety for command execution
        self._exec_lock = threading.Lock()

        self._logger = logging.getLogger(LogName.MAIN.value)

    # ========================================================================
    # Context Manager Support
    # ========================================================================

    def __enter__(self) -> "SshConnection":
        """Enter context manager.

        Returns:
            Self for context manager usage
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleanup connection.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.disconnect()

    # ========================================================================
    # Factory Methods
    # ========================================================================

    @classmethod
    def from_route(cls, route) -> "SshConnection":
        """Create SshConnection from Route configuration.

        Args:
            route: Route configuration with target and jump hosts

        Returns:
            Configured SshConnection instance
        """
        return cls(
            route.target.ip,
            route.target.username,
            route.target.password.get_secret_value(),
            route.jumps,
        )

    # ========================================================================
    # Connection Management
    # ========================================================================

    def connect(self) -> bool:
        """Establish SSH connection to target host.

        Returns:
            True if connection successful, False otherwise
        """
        if self.is_connected():
            self._logger.debug(f"{LogMsg.PRE_HOST_CON.value}{self._host}")
            return True

        self._logger.info(f"Connecting to {self._host} via {len(self._jump_hosts)} jump hosts")
        conn_start = time.perf_counter()

        try:
            self._ssh_client = self._create_client()

            if self._jump_hosts:
                self._logger.debug(
                    f"Using {len(self._jump_hosts)} jump hosts: {[j.ip for j in self._jump_hosts]}"
                )
                self._connect_via_jumps()
            else:
                self._logger.debug(f"Direct connection to host: {self._host}")
                self._ssh_client.connect(
                    self._host,
                    username=self._username,
                    password=self._password,
                    **self._SSH_DEFAULTS,
                )

            # Verify connection
            if not self.is_connected():
                self._logger.error(LogMsg.CON_TRANSPORT_INACTIVE.value)
                return False

            conn_time = (time.perf_counter() - conn_start) * 1000
            self._logger.debug(f"SSH connection established in {conn_time:.1f} ms")
            self._start_keepalive()
            self._logger.info(f"{LogMsg.CON_HOST_SUCCESS.value}{self._host}")
            return True

        except TimeoutError:
            self._logger.exception(f"{LogMsg.CON_TIMEOUT.value}{self._host}")
        except paramiko.AuthenticationException:
            self._logger.exception(f"{LogMsg.CON_AUTH_FAIL.value}{self._host}")
        except paramiko.SSHException:
            self._logger.exception(f"{LogMsg.CON_PROTOCOL_FAIL.value}{self._host}")
        except Exception:
            self._logger.exception(f"{LogMsg.CON_HOST_FAIL.value}{self._host}")

        self.disconnect()
        return False

    def disconnect(self) -> None:
        """Disconnect from host and cleanup resources."""
        if not self._ssh_client:
            self._logger.debug(f"{LogMsg.POST_HOST_DISCON.value}{self._host}")
            return

        self._logger.info(f"{LogMsg.DISCON_HOST.value}{self._host}")

        try:
            self._stop_keepalive.set()
            self._stop_keepalive_thread()
            self.close_shell()
            self._close_all_clients()
            self._logger.info(f"{LogMsg.DISCON_HOST_SUCCESS.value}{self._host}")

        except Exception:
            self._logger.exception(f"Error during disconnect from {self._host}")

    def is_connected(self) -> bool:
        """Check if SSH connection is active.

        Returns:
            True if connected, False otherwise
        """
        return self._ssh_client and (t := self._ssh_client.get_transport()) and t.is_active()

    def get_cr_log_common(self, cmd: str, lm: LogMsg) -> CmdResult:
        """Create error CmdResult with logging.

        Args:
            cmd: Command that failed
            lm: Log message enum

        Returns:
            CmdResult with error details
        """
        self._logger.warning(lm.value)
        cmd_result = CmdResult.error(cmd, lm.value)
        return cmd_result

    def get_cr_msg_connection(self, cmd: str, lm: LogMsg) -> CmdResult:
        """Create connection error CmdResult.

        Args:
            cmd: Command that failed
            lm: Log message enum

        Returns:
            CmdResult indicating no active connection
        """
        self._logger.error(f"{lm} - {cmd}")
        cmd_result = CmdResult.error(cmd, f"{lm} - {cmd}")
        return cmd_result

    # ========================================================================
    # Command Execution
    # ========================================================================

    def exec_cmd(
        self,
        cmd: str,
        timeout: int | None = 20,
        use_time_cmd: bool = False,
        logger: logging.Logger | None = None,
    ) -> CmdResult:
        """Execute command via SSH.

        Args:
            cmd: Command to execute
            timeout: Timeout in seconds (default: 20)
            use_time_cmd: Wrap command with 'time' for execution timing
            logger: Optional logger to use instead of default

        Returns:
            Command execution result
        """
        if not self.is_connected():
            return self.get_cr_msg_connection(cmd, LogMsg.CMD_CON)

        with self._exec_lock:
            log = logger or self._logger
            exec_cmd = cmd

            # Wrap with time command if requested
            if use_time_cmd:
                if self._sudo_pass:
                    escaped_cmd = cmd.replace("'", "'\"'\"'")
                    exec_cmd = f"time bash -c 'echo \"{self._sudo_pass}\" | sudo -S {escaped_cmd}'"
                else:
                    escaped_cmd = cmd.replace("'", "'\"'\"'")
                    exec_cmd = f"time bash -c '{escaped_cmd}'"
            elif self._sudo_pass and "sudo -S" not in cmd:
                exec_cmd = f'echo "{self._sudo_pass}" | sudo -S {cmd}'

            timeout_str = f" (timeout: {timeout} s)" if timeout is not None else ""
            log.debug(f"Executing command: '{exec_cmd}'{timeout_str}")

            try:
                start_time = time.perf_counter()
                _, stdout, stderr = self._ssh_client.exec_command(exec_cmd, timeout=timeout)
                send_time = (time.perf_counter() - start_time) * 1000

                read_start = time.perf_counter()
                stdout_data = self._clean(stdout.read().decode())
                stderr_data = self._clean(stderr.read().decode())
                rcode = stdout.channel.recv_exit_status()
                read_time = (time.perf_counter() - read_start) * 1000

                exec_time = time.perf_counter() - start_time

                # Parse time command output if present in stderr
                time_cmd_ms = 0.0
                if stderr_data and ("real" in stderr_data or "elapsed" in stderr_data):
                    time_parser = SutTimeParser(log.name)
                    time_parser.parse(stderr_data)
                    time_cmd_ms = time_parser.get_result()

                _log_exec_time(
                    exec_time,
                    rcode,
                    send_time,
                    read_time,
                    time_cmd_ms if time_cmd_ms > 0 else None,
                    log,
                )
                if rcode != 0:
                    log.warning(f"Command stderr: {stderr_data[:200]}")

                return CmdResult(
                    cmd=exec_cmd,
                    stdout=stdout_data,
                    stderr=stderr_data,
                    exec_time=exec_time,
                    rcode=rcode,
                    send_ms=send_time,
                    read_ms=read_time,
                    parsed_ms=time_cmd_ms,
                )

            except Exception as e:
                self._logger.exception(f"{LogMsg.AGENT_CMD_FAIL.value}{cmd}")
                return CmdResult(exec_cmd, "", f"Error: {e}", -1)

    def _clean(self, data: str) -> str:
        """Remove ANSI escape sequences from output.

        Args:
            data: Raw output string

        Returns:
            Cleaned string without ANSI codes
        """
        return re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", data)

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    def _create_client(self) -> paramiko.SSHClient:
        """Create configured SSH client.

        Returns:
            SSH client with AutoAddPolicy for host keys
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # noqa: S507
        return client

    def _connect_to_host(self, client: paramiko.SSHClient, host: Host, channel=None) -> None:
        """Connect SSH client to a host.

        Args:
            client: SSH client to use for connection
            host: Host configuration
            channel: Optional channel for tunneled connection
        """
        connect_args = {
            "username": host.username,
            "password": host.password.get_secret_value(),
            **self._SSH_DEFAULTS,
        }
        if channel:
            connect_args["sock"] = channel

        client.connect(host.ip, **connect_args)

    def _connect_via_jumps(self) -> None:
        """Connect to target through jump hosts.

        Establishes chain of SSH connections through each jump host,
        then connects to final target through the last jump host.

        Raises:
            ValueError: If no jump hosts provided
            RuntimeError: If transport unavailable
            Exception: On connection failures
        """
        if not self._jump_hosts:
            msg = "No jump hosts provided"
            raise ValueError(msg)

        transport = None
        self._logger.debug(f"Connecting through {len(self._jump_hosts)} jump hosts")

        for i, jump in enumerate(self._jump_hosts):
            self._logger.info(f"Connecting to jump host {i + 1}/{len(self._jump_hosts)}: {jump.ip}")
            client = self._create_client()

            try:
                if transport:
                    self._logger.debug(
                        f"Opening channel from {self._jump_hosts[i - 1].ip} to {jump.ip}"
                    )
                    channel = transport.open_channel(
                        "direct-tcpip", (jump.ip, 22), (self._jump_hosts[i - 1].ip, 22)
                    )
                    self._connect_to_host(client, jump, channel)
                else:
                    self._logger.debug(f"Direct connection to first jump host: {jump.ip}")
                    self._connect_to_host(client, jump)

                self._jump_clients.append(client)
                transport = client.get_transport()
                if not transport:
                    msg = f"No transport from {jump.ip}"
                    raise RuntimeError(msg)  # noqa: TRY301

                transport.set_keepalive(self._keepalive_interval)
                self._logger.info(f"{LogMsg.CON_JUMP_SUCCESS.value}{jump.ip}")

            except Exception:
                self._logger.exception(f"{LogMsg.CON_JUMP_FAIL.value}{jump.ip}")
                raise

        # Connect to target through final jump host
        if not transport:
            msg = "No transport available for target connection"
            raise RuntimeError(msg)

        self._logger.info(
            f"Opening final channel from {self._jump_hosts[-1].ip} to target {self._host}"
        )
        try:
            channel = transport.open_channel(
                "direct-tcpip", (self._host, 22), (self._jump_hosts[-1].ip, 22)
            )
            # Create temporary Host object for target
            target_host = Host(
                ip=self._host, username=self._username, password=SecretStr(self._password)
            )
            self._connect_to_host(self._ssh_client, target_host, channel)
            self._logger.debug(f"{LogMsg.CON_TARGET_SUCCESS.value}{self._host}")

        except Exception:
            self._logger.exception(f"{LogMsg.CON_HOST_FAIL.value}{self._host}")
            raise

    def _start_keepalive(self) -> None:
        """Start keepalive thread to maintain connection health."""
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()
        self._logger.debug("Keepalive thread started")

    def _keepalive_loop(self) -> None:
        """Keepalive loop that sends periodic packets to all connections.

        Runs in daemon thread until stop event is set.
        Logs warnings if no active connections found.
        """
        self._logger.debug(f"Keepalive loop started with {self._keepalive_interval}s interval")

        while not self._stop_keepalive.wait(self._keepalive_interval):
            try:
                active_count = 0
                total_count = 0

                for client in filter(None, [self._ssh_client, *self._jump_clients]):
                    total_count += 1
                    if (t := client.get_transport()) and t.is_active():
                        t.send_ignore()
                        active_count += 1

                self._logger.debug(
                    f"Keepalive sent to {active_count}/{total_count} active connections"
                )

                if active_count == 0 and total_count > 0:
                    self._logger.warning(LogMsg.ALIVE_NO_ACTIVE.value)

            except Exception:
                self._logger.exception(LogMsg.ALIVE_THREAD_FAIL.value)

        self._logger.debug("Keepalive loop stopped")

    # ========================================================================
    # Interactive Shell Management
    # ========================================================================

    def open_shell(self) -> bool:
        """Open interactive shell session.

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            self._logger.error(LogMsg.SHELL_NOT_CONNECTED.value)
            return False

        if self._shell:
            self._logger.debug(LogMsg.SHELL_ALREADY_OPEN.value)
            return True

        self._logger.info(f"Opening shell on {self._host}")

        try:
            self._shell = self._ssh_client.invoke_shell(width=120, height=40)
            self._logger.debug("Shell invoked, waiting for banner")

            # Wait longer for initial banner and send enter to activate prompt
            time.sleep(2)
            self._shell.send("\n")
            time.sleep(1)

            try:
                output = self._read_until_prompt(timeout=15)
                self._logger.debug(f"Shell opened. Initial banner length: {len(output)} chars")
                if output:
                    self._logger.debug(f"Banner preview:\n\n{output[:200]}...\n")
            except TimeoutError:
                self._logger.warning("Initial prompt detection failed, but continuing")
                output = ""

            # Configure SLX terminal - these commands may not work on all systems
            config_commands = [
                "terminal length 0"  # SLX specific
            ]

            for cmd in config_commands:
                try:
                    self._logger.debug(f"Executing config command: '{cmd}'")
                    self._shell.send(f"{cmd}\n")
                    time.sleep(0.5)
                except Exception:
                    self._logger.exception(f"Failed executing config command: '{cmd}'")

            # Clear buffer after config commands to prevent contamination
            try:
                self._read_until_prompt(timeout=2)
                self._logger.debug("Buffer cleared after config commands")
            except Exception:
                self._logger.exception("Buffer clear failed, continuing anyway")

            self._logger.info(LogMsg.SHELL_OPEN_SUCCESS.value)
            return True

        except Exception:
            self._logger.exception("Failed to open shell")
            if self._shell:
                try:  # noqa: SIM105
                    self._shell.close()
                except Exception:  # noqa: BLE001, S110
                    pass
                self._shell = None
            return False

    def _is_prompt_like(self, line: str) -> bool:
        """Check if line looks like a shell prompt.

        Args:
            line: Line to check

        Returns:
            True if line appears to be a prompt
        """
        return line.endswith(("$", "#", ">", ":")) or ":~$" in line or "Shell>" in line

    def _read_until_prompt(self, timeout: float = 10.0) -> str:
        """Read shell output until prompt detected.

        Args:
            timeout: Maximum seconds to wait for prompt

        Returns:
            Shell output as string

        Raises:
            ConnectionError: If shell not open
            TimeoutError: If prompt not detected within timeout
        """
        if not self._shell:
            msg = "Shell not open"
            raise ConnectionError(msg)

        buffer = b""
        start = time.time()
        self._logger.debug("Reading until prompt (timeout: %.1f s)", timeout)
        last_activity = start
        stable_count = 0

        while time.time() - start < timeout:
            if self._shell.recv_ready():
                chunk = self._shell.recv(4096)
                if chunk:
                    buffer += chunk
                    last_activity = time.time()
                    stable_count = 0
                    self._logger.debug(
                        f"Received {len(chunk)} bytes, total buffer: {len(buffer)} bytes"
                    )

                    # Check for prompt pattern
                    if self._prompt_pattern.search(buffer):
                        self._logger.debug("Prompt pattern matched!")
                        return buffer.decode(errors="ignore").strip()

                    # Also check last few lines for common prompt patterns
                    lines = buffer.decode(errors="ignore").splitlines()
                    if lines and self._is_prompt_like(lines[-1].strip()):
                        self._logger.debug(f"Detected prompt-like ending: '{lines[-1].strip()}'")
                        return buffer.decode(errors="ignore").strip()
            else:
                # No data ready, check if we've been stable
                if time.time() - last_activity > 2.0:  # 2 seconds of no activity
                    stable_count += 1
                    if stable_count > 3:  # Been stable for a while
                        self._logger.debug("No activity detected, assuming prompt ready")
                        if buffer:
                            return buffer.decode(errors="ignore").strip()
                time.sleep(0.1)

        self._logger.error(f"Timeout after {timeout:.1f} s. Buffer length: {len(buffer)}")
        if buffer:
            content = buffer.decode(errors="ignore")
            self._logger.error(f"Final buffer content: {content[-500:]}")
            # Return what we have instead of failing
            return content.strip()

        msg = "Prompt not detected within timeout"
        raise TimeoutError(msg)

    def exec_shell_cmd(
        self, cmd: str, *, until_prompt: bool = True, logger: logging.Logger | None = None
    ) -> str:
        """Execute command in interactive shell.

        Args:
            cmd: Command to execute
            until_prompt: Wait for prompt before returning
            logger: Optional logger to use instead of default

        Returns:
            Command output

        Raises:
            ConnectionError: If shell not open or connection lost
        """
        log = logger or self._logger

        if not self._shell:
            log.error(LogMsg.SHELL_CMD_NO_SHELL.value)
            msg = "Shell not opened"
            raise ConnectionError(msg)

        if not self.is_connected():
            log.error(LogMsg.SHELL_CMD_NO_CON.value)
            msg = "Connection lost"
            raise ConnectionError(msg)

        cmd_preview = cmd[:100] + "..." if len(cmd) > 100 else cmd
        log.debug(f"Executing shell command: {cmd_preview}")
        log.debug(f"Shell ready state: {self._shell.recv_ready()}")

        try:
            result = ""
            self._shell.send(cmd + "\n")

            if until_prompt:
                log.debug("Command sent, waiting for output...")

                output = self._read_until_prompt()
                log.debug(f"Raw output length: {len(output)}")

                if len(output) > 400:
                    log.debug(f"Raw output preview:\n\n{output[:200]}...{output[-200:]}\n")
                else:
                    log.debug(f"Raw output:\n\n{output}\n")

                # Clean up echoed command and prompt
                lines = output.splitlines()
                log.debug(f"Output has {len(lines)} lines")

                result = self._clean_shell_output(lines, cmd)
                log.debug(f"Clean output length: {len(result)}")
            else:
                log.debug("Command sent without waiting for prompt")

            return f"\n\n{result}\n\n"

        except Exception:
            log.exception(f"Shell cmd execution failed: '{cmd}'")
            raise

    def _clean_shell_output(self, lines: list[str], cmd: str) -> str:
        """Remove command echo and prompts from shell output.

        Args:
            lines: Output lines from shell
            cmd: Original command that was executed

        Returns:
            Cleaned output string
        """
        clean_lines = []
        for line in lines:
            # Skip the echoed command line
            if line.strip() == cmd.strip():
                continue
            # Skip prompt lines
            if re.search(self._prompt_pattern, line.encode()):
                continue
            clean_lines.append(line)

        return "\n".join(clean_lines).strip()

    def _stop_keepalive_thread(self) -> None:
        """Stop keepalive thread gracefully."""
        if not self._keepalive_thread:
            return

        self._logger.debug("Stopping keepalive thread")
        self._keepalive_thread.join(timeout=1)
        if self._keepalive_thread.is_alive():
            self._logger.warning(LogMsg.ALIVE_THREAD_STOP.value)
        self._keepalive_thread = None

    def _close_all_clients(self) -> None:
        """Close all SSH clients (main and jump hosts)."""
        all_clients = [self._ssh_client, *self._jump_clients]
        client_count = len([c for c in all_clients if c])
        self._logger.debug(f"Closing {client_count} connected clients")

        for i, client in enumerate(filter(None, all_clients)):
            try:
                client.close()
                self._logger.debug(f"Closed client {i + 1}/{client_count}")
            except Exception:
                self._logger.exception(f"Failed to close client {i + 1}")

        self._ssh_client = None
        self._jump_clients.clear()

    def close_shell(self) -> None:
        """Close interactive shell session."""
        if self._shell:
            try:
                self._logger.debug("Closing shell")
                self._shell.close()
                self._logger.debug("Shell closed successfully")
            except Exception:
                self._logger.exception("Error closing shell")
            finally:
                self._shell = None
        else:
            self._logger.debug("Shell already closed or not has not been opened")

    def clear_shell(self) -> None:
        """Clear shell buffer."""
        if not self._shell:
            self._logger.error("Shell not opened")
            return

        try:
            self._logger.debug("Clearing shell buffer")
            while self._shell.recv_ready():
                self._shell.recv(65536)
                time.sleep(0.1)
            self._logger.debug("Buffer cleared")
        except Exception:
            self._logger.exception("Error clearing shell buffer")
