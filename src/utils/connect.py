import logging
import threading
import time

import paramiko

from src.core.lifecycle import ILifecycleAware
from src.interfaces.connection import ConnectionResult, IConnection
from src.models.configurations import AppConfig, Host

logger = logging.getLogger(__name__)


class Ssh(IConnection, ILifecycleAware):
    """
    Handles an SSH tunnel through a jumphost to a final target.
    - connect()   : establishes both jump and target sessions.
    - disconnect(): cleanly closes both sessions.
    - exec_command(cmd): runs a command on the target host.
    A background thread sends a keep-alive packet every 30 seconds so the
    connections stay open forever (or until you call disconnect()).
    """

    def __init__(self, app_config: AppConfig, keepalive_interval: int = 30):
        self._app_config = app_config

        self.jump_hosts = [h for h in app_config.hosts if h.jump]
        self.target_host = [h for h in app_config.hosts if h.remote]  # this will always be one item

        self.keepalive_interval = keepalive_interval

        self._jump_ssh: paramiko.SSHClient | None = None
        self._target_ssh: paramiko.SSHClient | None = None

        self._keepalive_thread: threading.Thread | None = None
        self._stop_keepalive = threading.Event()

    def initialize(self) -> None:
        """Initialize connection (lifecycle interface)."""
        self.connect()

    def cleanup(self) -> None:
        """Clean up connection (lifecycle interface)."""
        self.disconnect()

    def __del__(self) -> None:
        """Cleanup on garbage collection."""
        self.disconnect()

    def __enter__(self) -> "Ssh":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.disconnect()

    # ---------------------------------------------------------------------------- #
    #                           Internal keep-alive logic                          #
    # ---------------------------------------------------------------------------- #

    def _keepalive_loop(self) -> None:
        """Send a keep-alive packet on each transport every *keepalive_interval* seconds."""
        while not self._stop_keepalive.is_set():
            if self._jump_ssh:
                transport = self._jump_ssh.get_transport()
                if transport and transport.is_active():
                    transport.send_ignore()
            if self._target_ssh:
                transport = self._target_ssh.get_transport()
                if transport and transport.is_active():
                    transport.send_ignore()
            time.sleep(self.keepalive_interval)

    # ---------------------------------------------------------------------------- #
    #                              Connection handling                             #
    # ---------------------------------------------------------------------------- #

    def _get_jump_hosts(self) -> list[Host]:
        """Get the jump hosts configurations sorted by jump_order."""
        jump_hosts = [h for h in self._app_config.hosts if h.jump]
        jump_hosts.sort(key=lambda h: h.jump_order or 0)
        return jump_hosts

    def _get_target_host(self) -> Host:
        """Get the remote host configuration."""
        if not self.target_host:
            msg = "No target host configured"
            raise RuntimeError(msg)

        return self.target_host[0]

    def connect(self) -> bool:
        """Open SSH sessions to the jumphost and then to the target via tunneleling."""
        try:
            jump_hosts = self._get_jump_hosts()
            target_host = self._get_target_host()

            if not jump_hosts:
                return self._connect_direct(target_host)

            return self._connect_via_jumps(jump_hosts, target_host)

        except Exception:
            logger.exception("Connection failed")
            self.disconnect()
            return False

    def _connect_direct(self, target_host: Host) -> bool:
        """Connect directly to target without jump hosts."""
        self._target_ssh = self._create_ssh_client()
        self._target_ssh.connect(
            hostname=target_host.ip,
            username=target_host.username,
            password=target_host.password.get_secret_value(),
            look_for_keys=False,
            allow_agent=False,
        )
        self._start_keepalive()
        return True

    def _connect_via_jumps(self, jump_hosts: list[Host], target_host: Host) -> bool:
        """Connect to target via jump hosts."""
        for index, host in enumerate(jump_hosts):
            self._jump_ssh = self._create_ssh_client()
            self._jump_ssh.connect(
                hostname=host.ip,
                username=host.username,
                password=host.password.get_secret_value(),
                look_for_keys=False,
                allow_agent=False,
            )

            jump_transport = self._jump_ssh.get_transport()
            if not jump_transport:
                raise RuntimeError("Failed to get transport from jump host.")

            jump_transport.set_keepalive(self.keepalive_interval)

            # Connect to target through last jump host
            if index + 1 == len(jump_hosts):
                channel = jump_transport.open_channel("direct-tcpip", (target_host.ip, 22), (host.ip, 22))

                try:
                    self._target_ssh = self._create_ssh_client()
                    self._target_ssh.connect(
                        hostname=target_host.ip,
                        username=target_host.username,
                        password=target_host.password.get_secret_value(),
                        sock=channel,
                        look_for_keys=False,
                        allow_agent=False,
                    )
                except Exception:
                    self._cleanup_jump_connection()
                    raise

                self._start_keepalive()
                break

        return True

    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _start_keepalive(self) -> None:
        """Start the keepalive thread."""
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def _cleanup_jump_connection(self) -> None:
        """Clean up jump connection on failure."""
        if self._jump_ssh:
            self._jump_ssh.close()
            self._jump_ssh = None

    def disconnect(self) -> None:
        """Terminate both SSH sessions and stop the keep-alive thread."""
        self._stop_keepalive.set()
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=1)

        if self._target_ssh:
            self._target_ssh.close()
            self._target_ssh = None

        if self._jump_ssh:
            self._jump_ssh.close()
            self._jump_ssh = None

    # ---------------------------------------------------------------------------- #
    #                               Command execution                              #
    # ---------------------------------------------------------------------------- #

    def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
        """Execute command and return structured result."""
        if not self._target_ssh:
            return ConnectionResult("", "Not connected - Call connect() first.", -1)

        try:
            _, stdout, stderr = self._target_ssh.exec_command(command, timeout=timeout)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()
            return_code = stdout.channel.recv_exit_status()

            return ConnectionResult(stdout_str, stderr_str, return_code)
        except Exception as e:
            logger.exception(f"Command execution failed: {command}")
            return ConnectionResult("", f"Execution error: {e}", -1)

    def exec_command(self, command: str, timeout: int | None = None) -> tuple[str, str]:
        """Legacy method for backward compatibility."""
        result = self.execute_command(command, timeout)
        return result.stdout, result.stderr

    # ---------------------------------------------------------------------------- #
    #                               Connection status                              #
    # ---------------------------------------------------------------------------- #

    def is_connected(self) -> bool:
        """Return True if target SSH transport is alive."""
        if not self._target_ssh:
            return False

        transport = self._target_ssh.get_transport()
        return transport is not None and transport.is_active()
