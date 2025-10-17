"""SSH connection with multi-jump support and keepalive."""

import logging
import re
import threading
import time
from typing import Any

import paramiko

from src.interfaces.connection import ConnectionResult, IConnection, IConnectionFactory
from src.models.config import Host, Route

logger = logging.getLogger(__name__)


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

    _SSH_DEFAULTS = {"look_for_keys": False, "allow_agent": False, "timeout": 30}

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
            rb"SLX#\s*$|\[.*@.*\]#\s*$|Password:\s*$|password for.*:\s*$|FBR\.\d+>\s*$", re.MULTILINE
        )

    @classmethod
    def from_route(cls, route: Route) -> "SshConnection":
        return cls(route.target.ip, route.target.username, route.target.password.get_secret_value(), route.jumps)

    def __enter__(self) -> "SshConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    def connect(self) -> bool:
        try:
            self._ssh_client = self._create_client()

            if self._jump_hosts:
                self._connect_via_jumps()
            else:
                self._ssh_client.connect(
                    self._host, username=self._username, password=self._password, **self._SSH_DEFAULTS
                )

            self._start_keepalive()
            return True
        except TimeoutError as e:
            logger.error("SSH connection timeout to %s: %s", self._host, e)
            self.disconnect()
            return False
        except paramiko.AuthenticationException as e:
            logger.error("SSH authentication failed for %s: %s", self._host, e)
            self.disconnect()
            return False
        except paramiko.SSHException as e:
            logger.error("SSH protocol error for %s: %s", self._host, e)
            self.disconnect()
            return False
        except Exception:
            logger.exception("SSH connection failed")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        self._stop_keepalive.set()

        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=1)
            self._keepalive_thread = None

        self.close_shell()

        for client in filter(None, [self._ssh_client] + self._jump_clients):
            client.close()

        self._ssh_client = None
        self._jump_clients.clear()

    def is_connected(self) -> bool:
        return self._ssh_client and (t := self._ssh_client.get_transport()) and t.is_active()

    def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
        if not self.is_connected():
            return ConnectionResult("", "Not connected", -1)

        try:
            _, stdout, stderr = self._ssh_client.exec_command(command, timeout=timeout)
            return ConnectionResult(stdout.read().decode(), stderr.read().decode(), stdout.channel.recv_exit_status())
        except Exception as e:
            logger.exception(f"Command failed: {command}")
            return ConnectionResult("", f"Error: {e}", -1)

    def exec_command(self, command: str, timeout: int | None = None) -> tuple[str, str]:
        r = self.execute_command(command, timeout)
        return r.stdout, r.stderr

    def _create_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _connect_via_jumps(self) -> None:
        transport = None

        for i, jump in enumerate(self._jump_hosts):
            client = self._create_client()

            if transport:
                channel = transport.open_channel("direct-tcpip", (jump.ip, 22), (self._jump_hosts[i - 1].ip, 22))
                client.connect(
                    jump.ip,
                    username=jump.username,
                    password=jump.password.get_secret_value(),
                    sock=channel,
                    **self._SSH_DEFAULTS,
                )
            else:
                client.connect(
                    jump.ip, username=jump.username, password=jump.password.get_secret_value(), **self._SSH_DEFAULTS
                )

            self._jump_clients.append(client)
            transport = client.get_transport()
            if not transport:
                raise RuntimeError(f"No transport from {jump.ip}")
            transport.set_keepalive(self._keepalive_interval)

        # Connect to target
        channel = transport.open_channel("direct-tcpip", (self._host, 22), (self._jump_hosts[-1].ip, 22))
        self._ssh_client.connect(
            self._host, username=self._username, password=self._password, sock=channel, **self._SSH_DEFAULTS
        )

    def _start_keepalive(self) -> None:
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        while not self._stop_keepalive.wait(self._keepalive_interval):
            try:
                for client in filter(None, [self._ssh_client] + self._jump_clients):
                    if (t := client.get_transport()) and t.is_active():
                        t.send_ignore()
            except Exception:
                logger.exception("Keepalive failed")

    def open_shell(self) -> bool:
        """Open interactive shell for SLX OS commands."""
        if not self.is_connected():
            logger.error("Cannot open shell: not connected")
            return False

        try:
            self._shell = self._ssh_client.invoke_shell()
            time.sleep(1)  # Wait for banner
            output = self._read_until_prompt()
            logger.debug(f"Shell opened. Initial banner:\n{output}")

            # Set terminal length to 0 to disable paging
            logger.debug("Setting terminal length to 0")
            self.execute_shell_command("terminal length 0")

            return True
        except Exception:
            logger.exception("Failed to open shell")
            return False

    def _read_until_prompt(self, timeout: float = 10.0) -> str:
        """Read shell output until prompt is detected or timeout occurs."""
        if not self._shell:
            raise ConnectionError("Shell not open")

        buffer = b""
        start = time.time()
        logger.debug(f"Starting to read until prompt with timeout {timeout}s")

        while time.time() - start < timeout:
            if self._shell.recv_ready():
                chunk = self._shell.recv(4096)
                buffer += chunk
                logger.debug(f"Received {len(chunk)} bytes, total buffer: {len(buffer)} bytes")
                logger.debug(f"Last 100 chars of buffer: {buffer[-100:]}")

                if self._prompt_pattern.search(buffer):
                    logger.debug("Prompt pattern matched!")
                    return buffer.decode(errors="ignore")
            else:
                time.sleep(0.1)

        logger.error(f"Timeout after {timeout}s. Buffer length: {len(buffer)}")
        logger.error(f"Final buffer content: {buffer.decode(errors='ignore')[-500:]}")
        raise TimeoutError("Prompt not detected within timeout")

    def execute_shell_command(self, command: str) -> str:
        """Send command to SLX shell and return output."""
        if not self._shell:
            raise ConnectionError("Shell not open")

        logger.info(f"Executing shell command: {command}")
        logger.debug(f"Shell ready state: {self._shell.recv_ready()}")

        self._shell.send(command + "\n")
        logger.debug("Command sent, waiting for output...")

        output = self._read_until_prompt()
        logger.debug(f"Raw output length: {len(output)}")
        logger.debug(f"Raw output preview: {output[:200]}...{output[-200:]}")

        # Clean up echoed command and prompt
        lines = output.splitlines()
        logger.debug(f"Output has {len(lines)} lines")

        clean_output = "\n".join(line for line in lines if not re.search(self._prompt_pattern, line.encode()))
        logger.debug(f"Clean output length: {len(clean_output)}")

        return clean_output.strip()

    def close_shell(self) -> None:
        """Close interactive shell."""
        if self._shell:
            self._shell.close()
            self._shell = None
            logger.debug("Shell closed")


class SshConnectionFactory(IConnectionFactory):
    def create_connection(self, config: Any) -> IConnection:
        password = (
            config.password.get_secret_value() if hasattr(config.password, "get_secret_value") else config.password
        )
        return SshConnection(
            getattr(config, "ip", "localhost"),
            getattr(config, "username", "user"),
            password,
            getattr(config, "jump_hosts", None),
        )
