"""SSH connection with multi-jump support and keepalive."""

import logging
import re
import threading
import time
from typing import Any, ClassVar

import paramiko

from src.core.enums.messages import LogMsg
from src.interfaces.component import IConnection
from src.interfaces.connection import CmdResult
from src.models.config import Host, Route
from src.platform.enums.log import LogName


class SshConnection(IConnection):
    """SSH connection class with jump host and keepalive support.

    Manages SSH connections with support for:
    - Direct connections to target hosts
    - Multi-hop connections through jump hosts
    - Automatic keepalive to maintain connection health
    - Interactive shell sessions
    - Command execution with timeout support
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

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        jump_hosts: list[Host] | None = None,
        keepalive_interval: int = 30,
    ):
        """Initialize SSH connection.

        Args:
            host: Target host IP or hostname
            username: SSH username
            password: SSH password
            jump_hosts: Optional list of jump hosts for multi-hop connection
            keepalive_interval: Seconds between keepalive packets
        """
        self._host = host
        self._username = username
        self._password = password
        self._jump_hosts = jump_hosts or []
        self._keepalive_interval = keepalive_interval
        self._ssh_client = None
        self._jump_clients = []
        self._keepalive_thread = None
        self._stop_keepalive = threading.Event()
        self._shell = None
        self._prompt_pattern = re.compile(
            self._PROMPT_PATTERN,
            re.MULTILINE,
        )

        self._logger = logging.getLogger(f"{LogName.MAIN.value}.{host}")

    def __enter__(self) -> "SshConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

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

    def connect(self) -> bool:
        """Establish SSH connection to target host.

        Connects directly or through jump hosts if configured.
        Starts keepalive thread on successful connection.

        Returns:
            True if connection successful, False otherwise
        """
        if self.is_connected():
            self._logger.debug("%s%s", LogMsg.PRE_HOST_CON.value, self._host)
            return True

        self._logger.info("Connecting to %s via %d jump hosts", self._host, len(self._jump_hosts))

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

            self._start_keepalive()
            self._logger.info("%s%s", LogMsg.CON_HOST_SUCCESS.value, self._host)
            return True

        except TimeoutError:
            self._logger.exception("%s%s", LogMsg.CON_TIMEOUT.value, self._host)
        except paramiko.AuthenticationException:
            self._logger.exception("%s%s", LogMsg.CON_AUTH_FAIL.value, self._host)
        except paramiko.SSHException:
            self._logger.exception("%s%s", LogMsg.CON_PROTOCOL_FAIL.value, self._host)
        except Exception:
            self._logger.exception("Connection failed to host: %s", self._host)

        self.disconnect()
        return False

    def disconnect(self) -> None:
        """Disconnect from host and cleanup resources.

        Stops keepalive thread, closes shell, and closes all SSH clients.
        Safe to call multiple times.
        """
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
            True if client exists and transport is active
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
        self._logger.error("%s - %s", LogMsg.CMD_CON.value, cmd)
        cmd_result = CmdResult.error(cmd, f"{LogMsg.CMD_CON.value} - {cmd}")
        return cmd_result

    def exec_cmd(self, cmd: str, timeout: int | None = None) -> CmdResult:
        """Execute command via SSH.

        Args:
            cmd: Command to execute
            timeout: Optional timeout in seconds

        Returns:
            CmdResult with stdout, stderr, return code, and execution time
        """
        if not self.is_connected():
            return self.get_cr_msg_connection(cmd, LogMsg.CMD_CON)

        self._logger.debug("Executing cmd: '%s' (timeout: %ss)", cmd, timeout)

        try:
            start_time = time.perf_counter()
            _, stdout, stderr = self._ssh_client.exec_command(cmd, timeout=timeout)
            execution_time = time.perf_counter() - start_time

            stdout_data = self._clean(stdout.read().decode())
            stderr_data = self._clean(stderr.read().decode())
            rcode = stdout.channel.recv_exit_status()

            self._logger.debug("Cmd completed in %.3fs with exit status %d", execution_time, rcode)
            if stderr_data:
                self._logger.warning("Cmd stderr: %s", stderr_data[:200])

            return CmdResult(
                cmd=cmd,
                stdout=stdout_data,
                stderr=stderr_data,
                exec_time=execution_time,
                rcode=rcode,
            )

        except Exception as e:
            self._logger.exception("Cmd execution failed: %s", cmd)
            return CmdResult(cmd, "", f"Error: {e}", -1)

    def _clean(self, data: str) -> str:
        """Remove ANSI escape sequences from output.

        Args:
            data: Raw output string

        Returns:
            Cleaned string without ANSI codes
        """
        return re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", data)

    def _create_client(self) -> paramiko.SSHClient:
        """Create configured SSH client.

        Returns:
            SSH client with AutoAddPolicy for host keys
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
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
            raise ValueError("No jump hosts provided")

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
                    raise RuntimeError(f"No transport from {jump.ip}")

                transport.set_keepalive(self._keepalive_interval)
                self._logger.info("%s%s", LogMsg.CON_JUMP_SUCCESS.value, jump.ip)

            except Exception:
                self._logger.exception("%s%s", LogMsg.CON_JUMP_FAIL.value, jump.ip)
                raise

        # Connect to target through final jump host
        if not transport:
            raise RuntimeError("No transport available for target connection")

        self._logger.info(
            "Opening final channel from %s to target %s", self._jump_hosts[-1].ip, self._host
        )
        try:
            channel = transport.open_channel(
                "direct-tcpip", (self._host, 22), (self._jump_hosts[-1].ip, 22)
            )
            # Create temporary Host object for target
            from pydantic import SecretStr

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

    def open_shell(self) -> bool:
        """Open interactive shell session.

        Invokes shell, waits for prompt, and configures terminal settings.

        Returns:
            True if shell opened successfully, False otherwise
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

            # Try to configure terminal - these commands may not work on all systems
            config_commands = [
                "export TERM=xterm",
                "stty -echo",  # Disable echo if possible
                "terminal length 0",  # SLX specific
                "set +H",  # Disable history expansion
            ]

            for config_cmd in config_commands:
                try:
                    self._logger.debug("Trying config cmd: %s", config_cmd)
                    self._shell.send(f"{config_cmd}\n")
                    time.sleep(0.5)
                except Exception:
                    self._logger.debug("Config cmd '%s' failed", config_cmd)

            self._logger.info(LogMsg.SHELL_OPEN_SUCCESS.value)

            return True

        except Exception:
            self._logger.exception("Failed to open shell")
            if self._shell:
                try:
                    self._shell.close()
                except:
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
        return (
            line.endswith("$")
            or line.endswith("#")
            or line.endswith(">")
            or ":~$" in line
            or line.endswith(":")
            or "Shell>" in line
        )

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
            raise ConnectionError("Shell not open")

        buffer = b""
        start = time.time()
        self._logger.debug("Reading until prompt (timeout: %.1fs)", timeout)
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

        raise TimeoutError("Prompt not detected within timeout")

    def execute_shell_command(self, cmd: str, until_prompt: bool = True) -> str:
        """Execute command in interactive shell.

        Args:
            cmd: Command to execute
            until_prompt: Wait for prompt before returning

        Returns:
            Command output with echo and prompts removed

        Raises:
            ConnectionError: If shell not open or connection lost
        """
        if not self._shell:
            self._logger.error(LogMsg.SHELL_CMD_NO_SHELL.value)
            raise ConnectionError("Shell not opened")

        if not self.is_connected():
            self._logger.error(LogMsg.SHELL_CMD_NO_CON.value)
            raise ConnectionError("Connection lost")

        cmd_preview = cmd[:100] + "..." if len(cmd) > 100 else cmd
        self._logger.debug("Executing shell cmd: %s", cmd_preview)
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
                    self._logger.debug("Raw output: %s", output)

                # Clean up echoed command and prompt
                lines = output.splitlines()
                self._logger.debug("Output has %d lines", len(lines))

                result = self._clean_shell_output(lines, cmd)
                self._logger.debug("Clean output length: %d", len(result))
            else:
                self._logger.debug("Command sent without waiting for prompt")

            return result

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
        """Close interactive shell session.

        Safe to call multiple times.
        """
        if self._shell:
            try:
                self._logger.debug("Closing shell")
                self._shell.close()
                self._logger.debug("Shell closed successfully")
            except Exception:
                self._logger.warning("Error closing shell")
            finally:
                self._shell = None
        else:
            self._logger.debug("Shell already closed or not opened")


# class SshConnectionFactory(IConnectionFactory):
#     def create_connection(self, config: Any) -> IConnection:
#         password = (
#             config.password.get_secret_value()
#             if hasattr(config.password, "get_secret_value")
#             else config.password
#         )
#         return SshConnection(
#             getattr(config, "ip", "localhost"),
#             getattr(config, "username", "user"),
#             password,
#             getattr(config, "jump_hosts", None),
#         )
