"""Independent connection management with improved reliability."""

from abc import ABC, abstractmethod
import contextlib
from dataclasses import dataclass
import logging
import threading
import time

import paramiko

from src.core.base import Component, Result

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConnectionConfig:
    """Connection configuration."""

    host: str
    port: int = 22
    username: str = ""
    password: str = ""
    timeout: int = 30
    keepalive_interval: int = 30


@dataclass(frozen=True)
class CommandResult:
    """Command execution result."""

    stdout: str
    stderr: str
    return_code: int
    success: bool

    @classmethod
    def create(cls, stdout: str, stderr: str, return_code: int) -> "CommandResult":
        return cls(stdout=stdout, stderr=stderr, return_code=return_code, success=return_code == 0)


class Connection(ABC):
    """Abstract connection interface."""

    @abstractmethod
    def connect(self) -> Result[None]:
        """Establish connection."""

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection."""

    @abstractmethod
    def execute(self, command: str, timeout: int | None = None) -> Result[CommandResult]:
        """Execute command."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected."""


class SshConnection(Connection, Component):
    """Independent SSH connection with automatic reconnection."""

    def __init__(self, config: ConnectionConfig):
        super().__init__(f"SSH-{config.host}")
        self._config = config
        self._client: paramiko.SSHClient | None = None
        self._keepalive_thread: threading.Thread | None = None
        self._stop_keepalive = threading.Event()
        self._connection_lock = threading.RLock()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 3

    def _do_initialize(self) -> None:
        """Initialize SSH connection."""
        # Connection is established on-demand

    def _do_cleanup(self) -> None:
        """Cleanup SSH connection."""
        self.disconnect()

    def connect(self) -> Result[None]:
        """Establish SSH connection with retry logic."""
        with self._connection_lock:
            try:
                if self.is_connected():
                    return Result.ok(None)

                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                self._client.connect(
                    hostname=self._config.host,
                    port=self._config.port,
                    username=self._config.username,
                    password=self._config.password,
                    timeout=self._config.timeout,
                    look_for_keys=False,
                    allow_agent=False,
                )

                self._start_keepalive()
                self._reconnect_attempts = 0

                self._logger.info(f"Connected to {self._config.host}")
                return Result.ok(None)

            except Exception as e:
                self._logger.exception(f"Connection failed to {self._config.host}")
                self.disconnect()
                return Result.fail(str(e))

    def disconnect(self) -> None:
        """Disconnect SSH connection."""
        with self._connection_lock:
            self._stop_keepalive.set()

            if self._keepalive_thread and self._keepalive_thread.is_alive():
                self._keepalive_thread.join(timeout=1)

            if self._client:
                with contextlib.suppress(Exception):
                    self._client.close()
                self._client = None

            self._logger.info(f"Disconnected from {self._config.host}")

    def execute(self, command: str, timeout: int | None = None) -> Result[CommandResult]:
        """Execute command with automatic reconnection."""
        if not command.strip():
            return Result.fail("Empty command")

        # Ensure connection
        if not self.is_connected():
            connect_result = self._reconnect()
            if not connect_result.success:
                return Result.fail(f"Connection failed: {connect_result.error}")

        try:
            with self._connection_lock:
                if not self._client:
                    return Result.fail("No active connection")

                stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout or self._config.timeout)

                stdout_data = stdout.read().decode("utf-8", errors="replace")
                stderr_data = stderr.read().decode("utf-8", errors="replace")
                return_code = stdout.channel.recv_exit_status()

                result = CommandResult.create(stdout_data, stderr_data, return_code)

                if not result.success:
                    self._logger.warning(f"Command failed: {command} (exit code: {return_code})")

                return Result.ok(result)

        except Exception as e:
            self._logger.exception(f"Command execution failed: {command}")
            # Try to reconnect for next command
            self._reconnect()
            return Result.fail(str(e))

    def is_connected(self) -> bool:
        """Check if connection is active."""
        with self._connection_lock:
            if not self._client:
                return False

            transport = self._client.get_transport()
            return transport is not None and transport.is_active()

    def _reconnect(self) -> Result[None]:
        """Attempt to reconnect with backoff."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            return Result.fail("Max reconnection attempts exceeded")

        self._reconnect_attempts += 1
        self._logger.info(f"Reconnection attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}")

        # Exponential backoff
        delay = min(2**self._reconnect_attempts, 30)
        time.sleep(delay)

        self.disconnect()
        return self.connect()

    def _start_keepalive(self) -> None:
        """Start keepalive thread."""
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop, daemon=True, name=f"keepalive-{self._config.host}"
        )
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        """Keepalive loop to maintain connection."""
        while not self._stop_keepalive.is_set():
            try:
                if self._client:
                    transport = self._client.get_transport()
                    if transport and transport.is_active():
                        transport.send_ignore()
                    else:
                        break
            except Exception:
                break

            time.sleep(self._config.keepalive_interval)


class JumpHostConnection(Connection, Component):
    """SSH connection through jump host."""

    def __init__(self, jump_config: ConnectionConfig, target_config: ConnectionConfig):
        super().__init__(f"Jump-{jump_config.host}->{target_config.host}")
        self._jump_config = jump_config
        self._target_config = target_config
        self._jump_client: paramiko.SSHClient | None = None
        self._target_client: paramiko.SSHClient | None = None
        self._connection_lock = threading.RLock()

    def _do_initialize(self) -> None:
        """Initialize jump host connection."""

    def _do_cleanup(self) -> None:
        """Cleanup jump host connection."""
        self.disconnect()

    def connect(self) -> Result[None]:
        """Connect through jump host."""
        with self._connection_lock:
            try:
                # Connect to jump host
                self._jump_client = paramiko.SSHClient()
                self._jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._jump_client.connect(
                    hostname=self._jump_config.host,
                    port=self._jump_config.port,
                    username=self._jump_config.username,
                    password=self._jump_config.password,
                    timeout=self._jump_config.timeout,
                    look_for_keys=False,
                    allow_agent=False,
                )

                # Create tunnel to target
                jump_transport = self._jump_client.get_transport()
                if not jump_transport:
                    msg = "Failed to get jump host transport"
                    raise RuntimeError(msg)

                dest_addr = (self._target_config.host, self._target_config.port)
                local_addr = (self._jump_config.host, self._jump_config.port)
                channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

                # Connect to target through tunnel
                self._target_client = paramiko.SSHClient()
                self._target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._target_client.connect(
                    hostname=self._target_config.host,
                    username=self._target_config.username,
                    password=self._target_config.password,
                    sock=channel,
                    timeout=self._target_config.timeout,
                    look_for_keys=False,
                    allow_agent=False,
                )

                self._logger.info(f"Connected through jump host {self._jump_config.host} to {self._target_config.host}")
                return Result.ok(None)

            except Exception as e:
                self._logger.exception("Jump host connection failed")
                self.disconnect()
                return Result.fail(str(e))

    def disconnect(self) -> None:
        """Disconnect from both jump and target hosts."""
        with self._connection_lock:
            if self._target_client:
                with contextlib.suppress(Exception):
                    self._target_client.close()
                self._target_client = None

            if self._jump_client:
                with contextlib.suppress(Exception):
                    self._jump_client.close()
                self._jump_client = None

    def execute(self, command: str, timeout: int | None = None) -> Result[CommandResult]:
        """Execute command on target host."""
        if not self.is_connected():
            connect_result = self.connect()
            if not connect_result.success:
                return Result.fail(f"Connection failed: {connect_result.error}")

        try:
            with self._connection_lock:
                if not self._target_client:
                    return Result.fail("No target connection")

                stdin, stdout, stderr = self._target_client.exec_command(
                    command, timeout=timeout or self._target_config.timeout
                )

                stdout_data = stdout.read().decode("utf-8", errors="replace")
                stderr_data = stderr.read().decode("utf-8", errors="replace")
                return_code = stdout.channel.recv_exit_status()

                result = CommandResult.create(stdout_data, stderr_data, return_code)
                return Result.ok(result)

        except Exception as e:
            self._logger.exception(f"Command execution failed: {command}")
            return Result.fail(str(e))

    def is_connected(self) -> bool:
        """Check if both connections are active."""
        with self._connection_lock:
            if not self._jump_client or not self._target_client:
                return False

            jump_transport = self._jump_client.get_transport()
            target_transport = self._target_client.get_transport()

            return (
                jump_transport is not None
                and jump_transport.is_active()
                and target_transport is not None
                and target_transport.is_active()
            )
