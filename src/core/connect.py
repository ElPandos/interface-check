"""SSH and local connection management."""

import logging
import re
import subprocess
import threading
import time
from typing import Any, ClassVar

import paramiko

from src.core.enums.messages import LogMsg
from src.core.parser import TimeCommandParser
from src.core.result import CmdResult
from src.interfaces.component import IConnection
from src.models.config import Host, Route
from src.platform.enums.log import LogName


def _log_exec_time(  # noqa: PLR0913
    exec_time: float,
    exit_code: int,
    send_time: float | None = None,
    read_time: float | None = None,
    time_cmd_ms: float | None = None,
    logger: logging.Logger | None = None,
) -> None:
    """Log command execution time.

    Args:
        exec_time: Total execution time in seconds
        exit_code: Command exit code
        send_time: Optional send time in milliseconds
        read_time: Optional read time in milliseconds
        time_cmd_ms: Optional parsed time from time command in milliseconds
        logger: Logger instance
    """
    exec_ms = exec_time * 1000
    if send_time is not None and read_time is not None:
        time_str = f", time={time_cmd_ms:.1f} ms" if time_cmd_ms else ""
        logger.debug(
            "Command execution times: send=%.1f ms, read=%.1f ms%s (exit: %d)",
            send_time,
            read_time,
            time_str,
            exit_code,
        )
    else:
        logger.debug("Command completed in %.1f ms with exit status: %d", exec_ms, exit_code)


class SshConnection(IConnection):
    """SSH connection with jump host and keepalive support.

    Manages SSH connections with multi-hop support through jump hosts.
    Includes automatic keepalive and shell session management.
    """

    __slots__ = (
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
    def from_route(cls, route: Route) -> "SshConnection":
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
            self._logger.debug("%s%s", LogMsg.PRE_HOST_CON.value, self._host)
            return True

        self._logger.info("Connecting to %s via %d jump hosts", self._host, len(self._jump_hosts))
        conn_start = time.perf_counter()

        try:
            self._ssh_client = self._create_client()

            if self._jump_hosts:
                self._logger.debug(
                    "Using %d jump hosts: %s",
                    len(self._jump_hosts),
                    [j.ip for j in self._jump_hosts],
                )
                self._connect_via_jumps()
            else:
                self._logger.debug("Direct connection to host: %s", self._host)
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
            self._logger.debug("SSH connection established in %.1f ms", conn_time)
            self._start_keepalive()
            self._logger.info("%s%s", LogMsg.CON_HOST_SUCCESS.value, self._host)
            return True  # noqa: TRY300

        except TimeoutError:
            self._logger.exception("%s%s", LogMsg.CON_TIMEOUT.value, self._host)
        except paramiko.AuthenticationException:
            self._logger.exception("%s%s", LogMsg.CON_AUTH_FAIL.value, self._host)
        except paramiko.SSHException:
            self._logger.exception("%s%s", LogMsg.CON_PROTOCOL_FAIL.value, self._host)
        except Exception:
            self._logger.exception("%s%s", LogMsg.CON_HOST_FAIL.value, self._host)

        self.disconnect()
        return False

    def disconnect(self) -> None:
        """Disconnect from host and cleanup resources."""
        if not self._ssh_client:
            self._logger.debug("%s%s", LogMsg.POST_HOST_DISCON.value, self._host)
            return

        self._logger.info("%s%s", LogMsg.DISCON_HOST.value, self._host)

        try:
            self._stop_keepalive.set()
            self._stop_keepalive_thread()
            self.close_shell()
            self._close_all_clients()
            self._logger.info("%s%s", LogMsg.DISCON_HOST_SUCCESS.value, self._host)

        except Exception:
            self._logger.exception("Error during disconnect from %s", self._host)

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
        self._logger.error("%s - %s", lm, cmd)
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
        log.debug("Executing command: '%s'%s", exec_cmd, timeout_str)

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
                time_parser = TimeCommandParser(log.name)
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
                log.warning("Command stderr: %s", stderr_data[:200])

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
            self._logger.exception("%s%s", LogMsg.AGENT_CMD_FAIL.value, cmd)
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
        self._logger.debug("Connecting through %d jump hosts", len(self._jump_hosts))

        for i, jump in enumerate(self._jump_hosts):
            self._logger.info(
                "Connecting to jump host %d/%d: %s", i + 1, len(self._jump_hosts), jump.ip
            )
            client = self._create_client()

            try:
                if transport:
                    self._logger.debug(
                        "Opening channel from %s to %s", self._jump_hosts[i - 1].ip, jump.ip
                    )
                    channel = transport.open_channel(
                        "direct-tcpip", (jump.ip, 22), (self._jump_hosts[i - 1].ip, 22)
                    )
                    self._connect_to_host(client, jump, channel)
                else:
                    self._logger.debug("Direct connection to first jump host: %s", jump.ip)
                    self._connect_to_host(client, jump)

                self._jump_clients.append(client)
                transport = client.get_transport()
                if not transport:
                    msg = f"No transport from {jump.ip}"
                    raise RuntimeError(msg)

                transport.set_keepalive(self._keepalive_interval)
                self._logger.info("%s%s", LogMsg.CON_JUMP_SUCCESS.value, jump.ip)

            except Exception:
                self._logger.exception("%s%s", LogMsg.CON_JUMP_FAIL.value, jump.ip)
                raise

        # Connect to target through final jump host
        if not transport:
            msg = "No transport available for target connection"
            raise RuntimeError(msg)

        self._logger.info(
            "Opening final channel from %s to target %s", self._jump_hosts[-1].ip, self._host
        )
        try:
            channel = transport.open_channel(
                "direct-tcpip", (self._host, 22), (self._jump_hosts[-1].ip, 22)
            )
            # Create temporary Host object for target
            from pydantic import SecretStr  # noqa: PLC0415

            target_host = Host(
                ip=self._host, username=self._username, password=SecretStr(self._password)
            )
            self._connect_to_host(self._ssh_client, target_host, channel)
            self._logger.debug("%s%s", LogMsg.CON_TARGET_SUCCESS.value, self._host)

        except Exception:
            self._logger.exception("%s%s", LogMsg.CON_HOST_FAIL.value, self._host)
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
        self._logger.debug("Keepalive loop started with %ds interval", self._keepalive_interval)

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
                    "Keepalive sent to %d/%d active connections", active_count, total_count
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

        self._logger.info("Opening shell on %s", self._host)

        try:
            self._shell = self._ssh_client.invoke_shell(width=120, height=40)
            self._logger.debug("Shell invoked, waiting for banner")

            # Wait longer for initial banner and send enter to activate prompt
            time.sleep(2)
            self._shell.send("\n")
            time.sleep(1)

            try:
                output = self._read_until_prompt(timeout=15)
                self._logger.debug("Shell opened. Initial banner length: %d chars", len(output))
                if output:
                    self._logger.debug("Banner preview: %s...", output[:200])
            except TimeoutError:
                self._logger.warning("Initial prompt detection failed, but continuing")
                output = ""

            # Configure SLX terminal - these commands may not work on all systems
            config_commands = [
                "terminal length 0"  # SLX specific
            ]

            for cmd in config_commands:
                try:
                    self._logger.debug("Executing config command: %s", cmd)
                    self._shell.send(f"{cmd}\n")
                    time.sleep(0.5)
                except Exception:
                    self._logger.exception("Failed executing config command: '%s'", cmd)

            # Clear buffer after config commands to prevent contamination
            try:
                self._read_until_prompt(timeout=2)
                self._logger.debug("Buffer cleared after config commands")
            except Exception:
                self._logger.exception("Buffer clear failed, continuing anyway")

            self._logger.info(LogMsg.SHELL_OPEN_SUCCESS.value)

            return True  # noqa: TRY300

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
                        "Received %d bytes, total buffer: %d bytes", len(chunk), len(buffer)
                    )

                    # Check for prompt pattern
                    if self._prompt_pattern.search(buffer):
                        self._logger.debug("Prompt pattern matched!")
                        return buffer.decode(errors="ignore")

                    # Also check last few lines for common prompt patterns
                    lines = buffer.decode(errors="ignore").splitlines()
                    if lines and self._is_prompt_like(lines[-1].strip()):
                        self._logger.debug("Detected prompt-like ending: '%s'", lines[-1].strip())
                        return buffer.decode(errors="ignore")
            else:
                # No data ready, check if we've been stable
                if time.time() - last_activity > 2.0:  # 2 seconds of no activity
                    stable_count += 1
                    if stable_count > 3:  # Been stable for a while
                        self._logger.debug("No activity detected, assuming prompt ready")
                        if buffer:
                            return buffer.decode(errors="ignore")
                time.sleep(0.1)

        self._logger.error("Timeout after %.1fs. Buffer length: %d", timeout, len(buffer))
        if buffer:
            content = buffer.decode(errors="ignore")
            self._logger.error("Final buffer content: %s", content[-500:])
            # Return what we have instead of failing
            return content

        msg = "Prompt not detected within timeout"
        raise TimeoutError(msg)

    def exec_shell_command(self, cmd: str, until_prompt: bool = True) -> str:  # noqa: FBT001, FBT002
        """Execute command in interactive shell.

        Args:
            cmd: Command to execute
            until_prompt: Wait for prompt before returning

        Returns:
            Command output

        Raises:
            ConnectionError: If shell not open or connection lost
        """
        if not self._shell:
            self._logger.error(LogMsg.SHELL_CMD_NO_SHELL.value)
            msg = "Shell not opened"
            raise ConnectionError(msg)

        if not self.is_connected():
            self._logger.error(LogMsg.SHELL_CMD_NO_CON.value)
            msg = "Connection lost"
            raise ConnectionError(msg)

        cmd_preview = cmd[:100] + "..." if len(cmd) > 100 else cmd
        self._logger.debug("Executing shell command: %s", cmd_preview)
        self._logger.debug("Shell ready state: %s", self._shell.recv_ready())

        try:
            result = ""
            self._shell.send(cmd + "\n")

            if until_prompt:
                self._logger.debug("Command sent, waiting for output...")

                output = self._read_until_prompt()
                self._logger.debug("Raw output length: %d", len(output))

                if len(output) > 400:
                    self._logger.debug("Raw output preview: %s...%s", output[:200], output[-200:])
                else:
                    self._logger.debug("Raw output:\n%s", output)

                # Clean up echoed command and prompt
                lines = output.splitlines()
                self._logger.debug("Output has %d lines", len(lines))

                result = self._clean_shell_output(lines, cmd)
                self._logger.debug("Clean output length: %d", len(result))
            else:
                self._logger.debug("Command sent without waiting for prompt")

            return result  # noqa: TRY300

        except Exception:
            self._logger.exception("Shell cmd execution failed: %s", cmd)
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
        self._logger.debug("Closing %d connected clients", client_count)

        for i, client in enumerate(filter(None, all_clients)):
            try:
                client.close()
                self._logger.debug("Closed client %d/%d", i + 1, client_count)
            except Exception:
                self._logger.exception("Failed to close client %d", i + 1)

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


class LocalConnection(IConnection):
    """Local command execution without SSH overhead.

    Executes commands directly on the local system using subprocess.
    """

    __slots__ = ("_host", "_logger", "_sudo_pass")

    def __init__(self, host: str = "localhost", sudo_pass: str = ""):
        """Initialize local connection.

        Args:
            host: Host identifier for logging (default: localhost)
            sudo_pass: Optional sudo password for privileged commands
        """
        self._host = host
        self._sudo_pass = sudo_pass

        self._logger = logging.getLogger(f"{LogName.MAIN.value}.{host}")

    def __enter__(self) -> "LocalConnection":
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.disconnect()

    def connect(self) -> bool:
        """Establish local connection (always succeeds).

        Returns:
            True
        """
        self._logger.debug("Using local command execution (no SSH)")
        return True

    def disconnect(self) -> None:
        """Disconnect (no-op for local execution)."""
        self._logger.debug("Local connection closed")

    def is_connected(self) -> bool:
        """Check if connection is active.

        Returns:
            True (always connected for local execution)
        """
        return True

    def exec_cmd(
        self,
        cmd: str,
        timeout: int | None = 20,
        use_time_cmd: bool = False,
        logger: logging.Logger | None = None,
    ) -> CmdResult:
        """Execute command locally.

        Args:
            cmd: Command to execute
            timeout: Timeout in seconds (default: 20)
            use_time_cmd: Wrap command with 'time' for execution timing
            logger: Optional logger to use instead of default

        Returns:
            Command execution result
        """
        exec_cmd = cmd
        log = logger or self._logger

        # Wrap with time command if requested
        if use_time_cmd:
            if self._sudo_pass:
                escaped_cmd = cmd.replace("'", "'\"'\"'")
                exec_cmd = f"time bash -c 'echo \"{self._sudo_pass}\" | sudo -S {escaped_cmd}'"
            else:
                escaped_cmd = cmd.replace("'", "'\"'\"'")
                exec_cmd = f"time bash -c '{escaped_cmd}'"
        elif self._sudo_pass and not cmd.startswith("sudo"):
            exec_cmd = f"sudo -S {cmd}"

        log.debug("Executing local command: '%s' (timeout: %s s)", exec_cmd, timeout)

        try:
            # Pass sudo password via stdin if needed (only when not using time_cmd)
            use_sudo = self._sudo_pass and not cmd.startswith("sudo") and not use_time_cmd
            stdin_input = f"{self._sudo_pass}\n" if use_sudo else None

            # For local execution, we measure total time as both send and read
            exec_start = time.perf_counter()
            result = subprocess.run(
                exec_cmd,
                shell=True,
                capture_output=True,
                text=True,
                input=stdin_input,
                timeout=timeout,
                check=False,
            )
            exec_time = time.perf_counter() - exec_start

            # Parse time command output if present in stderr
            parsed_ms = 0.0
            if result.stderr and ("real" in result.stderr or "elapsed" in result.stderr):
                time_parser = TimeCommandParser(log.name)
                time_parser.parse(result.stderr)
                parsed_ms = time_parser.get_result()

            # For local execution, no network send/read times
            _log_exec_time(
                exec_time,
                result.returncode,
                0.0,
                0.0,
                parsed_ms if parsed_ms > 0 else None,
                log,
            )

            if result.returncode != 0:
                log.warning("Command stderr: %s", result.stderr[:200])

            return CmdResult(
                cmd=exec_cmd,
                stdout=result.stdout,
                stderr=result.stderr,
                exec_time=exec_time / 1000,
                rcode=result.returncode,
                send_ms=0.0,
                read_ms=0.0,
                parsed_ms=parsed_ms,
            )

        except subprocess.TimeoutExpired:
            log.exception("Command timeout: %s", cmd)
            return CmdResult(exec_cmd, "", "Timeout", -1)
        except Exception as e:
            log.exception("Command execution failed: %s", cmd)
            return CmdResult(exec_cmd, "", f"Error: {e}", -1)
