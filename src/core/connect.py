"""SSH connection with multi-jump support and keepalive."""

import logging
import re
import threading
import time
from typing import Any, ClassVar

import paramiko

from src.interfaces.connection import CommandResult, IConnection, IConnectionFactory
from src.models.config import Host, Route


class SshConnection(IConnection):
    """SSH connection manager with jump host and keepalive support."""

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

        self.logger = logging.getLogger(f"{__name__}.{host}")
        self.logger.info(
            f"Initializing SSH connection to {host} with {len(self._jump_hosts)} jump hosts"
        )

    @classmethod
    def from_route(cls, route: Route) -> "SshConnection":
        return cls(
            route.target.ip,
            route.target.username,
            route.target.password.get_secret_value(),
            route.jumps,
        )

    def __enter__(self) -> "SshConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def connect(self) -> bool:
        if self.is_connected():
            self.logger.info("Already connected to %s", self._host)
            return True

        self.logger.info(f"Connecting to {self._host} via {len(self._jump_hosts)} jump hosts")

        try:
            self._ssh_client = self._create_client()

            if self._jump_hosts:
                self.logger.debug(f"Using jump hosts: {[j.ip for j in self._jump_hosts]}")
                self._connect_via_jumps()
            else:
                self.logger.debug(f"Direct connection to {self._host}")
                self._ssh_client.connect(
                    self._host,
                    username=self._username,
                    password=self._password,
                    **self._SSH_DEFAULTS,
                )

            # Verify connection
            if not self.is_connected():
                self.logger.error("Connection established but transport is not active")
                return False

            self._start_keepalive()
            self.logger.info(f"Successfully connected to {self._host}")
            return True

        except TimeoutError as e:
            self.logger.error(f"SSH connection timeout to {self._host}: {e}")
        except paramiko.AuthenticationException as e:
            self.logger.error(f"SSH authentication failed for {self._host}: {e}")
        except paramiko.SSHException as e:
            self.logger.error(f"SSH protocol error for {self._host}: {e}")
        except Exception as e:
            self.logger.exception(f"SSH connection failed to {self._host}: {e}")

        self.disconnect()
        return False

    def disconnect(self) -> None:
        if not self._ssh_client:
            self.logger.debug("Already disconnected")
            return

        self.logger.info(f"Disconnecting from {self._host}")

        try:
            self._stop_keepalive.set()

            if self._keepalive_thread:
                self.logger.debug("Stopping keepalive thread")
                self._keepalive_thread.join(timeout=1)
                if self._keepalive_thread.is_alive():
                    self.logger.warning("Keepalive thread did not stop gracefully")
                self._keepalive_thread = None

            self.close_shell()

            # Close all clients
            client_count = len([c for c in [self._ssh_client, *self._jump_clients] if c])
            self.logger.debug(f"Closing {client_count} SSH clients")

            for i, client in enumerate(filter(None, [self._ssh_client, *self._jump_clients])):
                try:
                    client.close()
                    self.logger.debug(f"Closed client {i + 1}/{client_count}")
                except Exception as e:
                    self.logger.warning(f"Error closing client {i + 1}: {e}")

            self._ssh_client = None
            self._jump_clients.clear()
            self.logger.info(f"Disconnected from {self._host}")

        except Exception as e:
            self.logger.exception(f"Error during disconnect from {self._host}: {e}")

    def is_connected(self) -> bool:
        return self._ssh_client and (t := self._ssh_client.get_transport()) and t.is_active()

    def execute_command(self, command: str, timeout: int | None = None) -> CommandResult:
        if not self.is_connected():
            self.logger.error(f"Cannot execute command '{command}': not connected")
            return CommandResult("", "Not connected", -1)

        self.logger.debug(f"Executing command: {command} (timeout: {timeout})")

        try:
            start_time = time.perf_counter()
            _, stdout, stderr = self._ssh_client.exec_command(command, timeout=timeout)
            execution_time = time.perf_counter() - start_time

            stdout_data = stdout.read().decode()
            stderr_data = stderr.read().decode()
            exit_status = stdout.channel.recv_exit_status()

            self.logger.debug(f"Command completed with exit status {exit_status}")
            if stderr_data:
                self.logger.warning(f"Command stderr: {stderr_data[:200]}")

            return CommandResult(stdout_data, stderr_data, execution_time, exit_status)

        except Exception as e:
            self.logger.exception(f"Command execution failed: {command}")
            return CommandResult("", f"Error: {e}", -1)

    def _create_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _connect_via_jumps(self) -> None:
        if not self._jump_hosts:
            raise ValueError("No jump hosts provided")

        transport = None
        self.logger.debug(f"Connecting through {len(self._jump_hosts)} jump hosts")

        for i, jump in enumerate(self._jump_hosts):
            self.logger.debug(f"Connecting to jump host {i + 1}/{len(self._jump_hosts)}: {jump.ip}")
            client = self._create_client()

            try:
                if transport:
                    self.logger.debug(
                        f"Opening channel from {self._jump_hosts[i - 1].ip} to {jump.ip}"
                    )
                    channel = transport.open_channel(
                        "direct-tcpip", (jump.ip, 22), (self._jump_hosts[i - 1].ip, 22)
                    )
                    client.connect(
                        jump.ip,
                        username=jump.username,
                        password=jump.password.get_secret_value(),
                        sock=channel,
                        **self._SSH_DEFAULTS,
                    )
                else:
                    self.logger.debug(f"Direct connection to first jump host: {jump.ip}")
                    client.connect(
                        jump.ip,
                        username=jump.username,
                        password=jump.password.get_secret_value(),
                        **self._SSH_DEFAULTS,
                    )

                self._jump_clients.append(client)
                transport = client.get_transport()
                if not transport:
                    raise RuntimeError(f"No transport from {jump.ip}")

                transport.set_keepalive(self._keepalive_interval)
                self.logger.debug(f"Successfully connected to jump host {jump.ip}")

            except Exception as e:
                self.logger.error(f"Failed to connect to jump host {jump.ip}: {e}")
                raise

        # Connect to target through final jump host
        if not transport:
            raise RuntimeError("No transport available for target connection")

        self.logger.debug(
            f"Opening final channel from {self._jump_hosts[-1].ip} to target {self._host}"
        )
        try:
            channel = transport.open_channel(
                "direct-tcpip", (self._host, 22), (self._jump_hosts[-1].ip, 22)
            )
            self._ssh_client.connect(
                self._host,
                username=self._username,
                password=self._password,
                sock=channel,
                **self._SSH_DEFAULTS,
            )
            self.logger.debug(f"Successfully connected to target {self._host}")

        except Exception as e:
            self.logger.error(f"Failed to connect to target {self._host}: {e}")
            raise

    def _start_keepalive(self) -> None:
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        self.logger.debug(f"Starting keepalive loop with {self._keepalive_interval}s interval")

        while not self._stop_keepalive.wait(self._keepalive_interval):
            try:
                active_count = 0
                total_count = 0

                for client in filter(None, [self._ssh_client, *self._jump_clients]):
                    total_count += 1
                    if (t := client.get_transport()) and t.is_active():
                        t.send_ignore()
                        active_count += 1

                self.logger.debug(
                    f"Keepalive sent to {active_count}/{total_count} active connections"
                )

                if active_count == 0 and total_count > 0:
                    self.logger.warning("No active connections found during keepalive")

            except Exception as e:
                self.logger.exception(f"Keepalive failed: {e}")

        self.logger.debug("Keepalive loop stopped")

    def open_shell(self) -> bool:
        """Open interactive shell for SLX OS commands."""
        if not self.is_connected():
            self.logger.error("Cannot open shell: not connected")
            return False

        if self._shell:
            self.logger.debug("Shell already open")
            return True

        self.logger.info(f"Opening shell on {self._host}")

        try:
            self._shell = self._ssh_client.invoke_shell(width=120, height=40)
            self.logger.debug("Shell invoked, waiting for banner")

            # Wait longer for initial banner and send enter to activate prompt
            time.sleep(2)
            self._shell.send("\n")
            time.sleep(1)

            try:
                output = self._read_until_prompt(
                    timeout=15
                )  # Longer timeout for initial connection
                self.logger.debug(f"Shell opened. Initial banner length: {len(output)} chars")
                self.logger.debug(f"Banner preview: {output[:200]}...")
            except TimeoutError:
                self.logger.warning("Initial prompt detection failed, but continuing")
                output = ""

            # Try to configure terminal - these commands may not work on all systems
            config_commands = [
                "export TERM=xterm",
                "stty -echo",  # Disable echo if possible
                "terminal length 0",  # SLX specific
                "set +H",  # Disable history expansion
            ]

            for cmd in config_commands:
                try:
                    self.logger.debug(f"Trying config command: {cmd}")
                    self._shell.send(f"{cmd}\n")
                    time.sleep(0.5)
                except Exception as e:
                    self.logger.debug(f"Config command '{cmd}' failed: {e}")

            self.logger.info("Shell opened and configured")

            return True

        except Exception as e:
            self.logger.exception(f"Failed to open shell: {e}")
            if self._shell:
                try:
                    self._shell.close()
                except:
                    pass
                self._shell = None
            return False

    def _read_until_prompt(self, timeout: float = 10.0) -> str:
        """Read shell output until prompt is detected or timeout occurs."""
        if not self._shell:
            raise ConnectionError("Shell not open")

        buffer = b""
        start = time.time()
        self.logger.debug(f"Starting to read until prompt with timeout {timeout}s")
        last_activity = start
        stable_count = 0

        while time.time() - start < timeout:
            if self._shell.recv_ready():
                chunk = self._shell.recv(4096)
                if chunk:
                    buffer += chunk
                    last_activity = time.time()
                    stable_count = 0
                    self.logger.debug(
                        f"Received {len(chunk)} bytes, total buffer: {len(buffer)} bytes"
                    )

                    # Check for prompt pattern
                    if self._prompt_pattern.search(buffer):
                        self.logger.debug("Prompt pattern matched!")
                        return buffer.decode(errors="ignore")

                    # Also check last few lines for common prompt patterns
                    lines = buffer.decode(errors="ignore").splitlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if (
                            last_line.endswith("$")
                            or last_line.endswith("#")
                            or last_line.endswith(">")
                            or ":~$" in last_line
                            or last_line.endswith(":")
                            or "Shell>" in last_line
                        ):
                            self.logger.debug(f"Detected prompt-like ending: '{last_line}'")
                            return buffer.decode(errors="ignore")
            else:
                # No data ready, check if we've been stable
                if time.time() - last_activity > 2.0:  # 2 seconds of no activity
                    stable_count += 1
                    if stable_count > 3:  # Been stable for a while
                        self.logger.debug("No activity detected, assuming prompt ready")
                        if buffer:
                            return buffer.decode(errors="ignore")
                time.sleep(0.1)

        self.logger.error(f"Timeout after {timeout}s. Buffer length: {len(buffer)}")
        if buffer:
            content = buffer.decode(errors="ignore")
            self.logger.error(f"Final buffer content: {content[-500:]}")
            # Return what we have instead of failing
            return content

        raise TimeoutError("Prompt not detected within timeout")

    def execute_shell_command(self, command: str, until_prompt: bool = True) -> str:
        """Send command to SLX shell and return output."""
        if not self._shell:
            self.logger.error("Cannot execute shell command: shell not opened")
            raise ConnectionError("Shell not opened")

        if not self.is_connected():
            self.logger.error("Cannot execute shell command: connection lost")
            raise ConnectionError("Connection lost")

        self.logger.debug(
            f"Executing shell command: {command[:100]}{'...' if len(command) > 100 else ''}"
        )
        self.logger.debug(f"Shell ready state: {self._shell.recv_ready()}")

        try:
            result = ""
            self._shell.send(command + "\n")

            if until_prompt:
                self.logger.debug("Command sent, waiting for output...")

                output = self._read_until_prompt()
                self.logger.debug(f"Raw output length: {len(output)}")

                if len(output) > 400:
                    self.logger.debug(f"Raw output preview: {output[:200]}...{output[-200:]}")
                else:
                    self.logger.debug(f"Raw output: {output}")

                # Clean up echoed command and prompt
                lines = output.splitlines()
                self.logger.debug(f"Output has {len(lines)} lines")

                # Filter out command echo and prompts
                clean_lines = []
                for line in lines:
                    # Skip the echoed command line
                    if line.strip() == command.strip():
                        continue
                    # Skip prompt lines
                    if re.search(self._prompt_pattern, line.encode()):
                        continue
                    clean_lines.append(line)

                result = "\n".join(clean_lines).strip()
                self.logger.debug(f"Clean output length: {len(result)}")
            else:
                self.logger.debug("Command sent without waiting for prompt")

            return result

        except Exception:
            self.logger.exception(f"Shell command execution failed: {command}")
            raise

    def close_shell(self) -> None:
        """Close interactive shell."""
        if self._shell:
            try:
                self.logger.debug("Closing shell")
                self._shell.close()
                self.logger.debug("Shell closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing shell: {e}")
            finally:
                self._shell = None
        else:
            self.logger.debug("Shell already closed or not opened")


class SshConnectionFactory(IConnectionFactory):
    def create_connection(self, config: Any) -> IConnection:
        password = (
            config.password.get_secret_value()
            if hasattr(config.password, "get_secret_value")
            else config.password
        )
        return SshConnection(
            getattr(config, "ip", "localhost"),
            getattr(config, "username", "user"),
            password,
            getattr(config, "jump_hosts", None),
        )
