# import logging
# import threading
# import time

# import paramiko

# from src.core.lifecycle import ILifecycleAware
# from src.interfaces.connection import ConnectionResult, IConnection
# from src.models.config import Config, Host, Route

# logger = logging.getLogger(__name__)


# class Ssh(IConnection, ILifecycleAware):
#     """
#     Handles an SSH tunnel through a jumphost to a final target.
#     - connect()   : establishes both jump and target sessions.
#     - disconnect(): cleanly closes both sessions.
#     - exec_command(cmd): runs a command on the target host.
#     A background thread sends a keep-alive packet every 30 seconds so the
#     connections stay open forever (or until you call disconnect()).
#     """

#     def __init__(self, config: Config, route: Route | None = None, keepalive_interval: int = 30):
#         self._config = config
#         self._route = route or (config.networks.routes[0] if config.network.routes else None)

#         if not self._route:
#             msg = "No route specified and no default route available"
#             raise ValueError(msg)

#         self.keepalive_interval = keepalive_interval

#         self._jump_ssh: paramiko.SSHClient | None = None
#         self._target_ssh: paramiko.SSHClient | None = None

#         self._keepalive_thread: threading.Thread | None = None
#         self._stop_keepalive = threading.Event()

#     def initialize(self) -> None:
#         """Initialize connection (lifecycle interface)."""
#         self.connect()

#     def cleanup(self) -> None:
#         """Clean up connection (lifecycle interface)."""
#         self.disconnect()

#     def __del__(self) -> None:
#         """Cleanup on garbage collection."""
#         from contextlib import suppress

#         with suppress(AttributeError):
#             self.disconnect()

#     def __enter__(self) -> "Ssh":
#         """Context manager entry."""
#         self.connect()
#         return self

#     def __exit__(self, exc_type, exc_val, exc_tb) -> None:
#         """Context manager exit - ensures cleanup."""
#         self.disconnect()

#     # ---------------------------------------------------------------------------- #
#     #                           Internal keep-alive logic                          #
#     # ---------------------------------------------------------------------------- #

#     def _keepalive_loop(self) -> None:
#         """Send a keep-alive packet on each transport every *keepalive_interval* seconds."""
#         while not self._stop_keepalive.is_set():
#             if self._jump_ssh:
#                 transport = self._jump_ssh.get_transport()
#                 if transport and transport.is_active():
#                     transport.send_ignore()
#             if self._target_ssh:
#                 transport = self._target_ssh.get_transport()
#                 if transport and transport.is_active():
#                     transport.send_ignore()
#             time.sleep(self.keepalive_interval)

#     # ---------------------------------------------------------------------------- #
#     #                              Connection handling                             #
#     # ---------------------------------------------------------------------------- #

#     def _get_jump_hosts(self) -> list[Host]:
#         """Get the jump hosts configurations sorted by order."""
#         if not self._route:
#             return []

#         # Sort hops by order and return the hosts
#         sorted_hops = sorted(self._route.hops, key=lambda hop: hop.order)
#         return [hop.host for hop in sorted_hops]

#     def _get_target_host(self) -> Host:
#         """Get the target host configuration."""
#         if not self._route:
#             msg = "No route configured"
#             raise RuntimeError(msg)

#         return self._route.destination

#     def connect(self) -> bool:
#         """Open SSH sessions to the jumphost and then to the target via tunneleling."""
#         try:
#             jump_hosts = self._get_jump_hosts()
#             target_host = self._get_target_host()

#             if not jump_hosts:
#                 return self._connect_direct(target_host)

#             return self._connect_via_jumps(jump_hosts, target_host)

#         except Exception:
#             logger.exception("Connection failed")
#             self.disconnect()
#             return False

#     def _connect_direct(self, target_host: Host) -> bool:
#         """Connect directly to target without jump hosts."""
#         self._target_ssh = self._create_ssh_client()
#         self._target_ssh.connect(
#             hostname=target_host.address,
#             username=target_host.username,
#             password=target_host.password.get_secret_value(),
#             look_for_keys=False,
#             allow_agent=False,
#         )
#         self._start_keepalive()
#         return True

#     def _connect_via_jumps(self, jump_hosts: list[Host], target_host: Host) -> bool:
#         """Connect to target via jump hosts."""
#         for index, host in enumerate(jump_hosts):
#             self._jump_ssh = self._create_ssh_client()
#             self._jump_ssh.connect(
#                 hostname=host.address,
#                 username=host.username,
#                 password=host.password.get_secret_value(),
#                 look_for_keys=False,
#                 allow_agent=False,
#             )

#             jump_transport = self._jump_ssh.get_transport()
#             if not jump_transport:
#                 msg = "Failed to get transport from jump host."
#                 raise RuntimeError(msg)

#             jump_transport.set_keepalive(self.keepalive_interval)

#             # Connect to target through last jump host
#             if index + 1 == len(jump_hosts):
#                 channel = jump_transport.open_channel("direct-tcpip", (target_host.address, 22), (host.address, 22))

#                 try:
#                     self._target_ssh = self._create_ssh_client()
#                     self._target_ssh.connect(
#                         hostname=target_host.address,
#                         username=target_host.username,
#                         password=target_host.password.get_secret_value(),
#                         sock=channel,
#                         look_for_keys=False,
#                         allow_agent=False,
#                     )
#                 except Exception:
#                     self._cleanup_jump_connection()
#                     raise

#                 self._start_keepalive()
#                 break

#         return True

#     def _create_ssh_client(self) -> paramiko.SSHClient:
#         """Create and configure SSH client."""
#         self._client = paramiko.SSHClient()
#         self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#         return self._client

#     def _start_keepalive(self) -> None:
#         """Start the keepalive thread."""
#         self._stop_keepalive.clear()
#         self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
#         self._keepalive_thread.start()

#     def _cleanup_jump_connection(self) -> None:
#         """Clean up jump connection on failure."""
#         if self._jump_ssh:
#             self._jump_ssh.close()
#             self._jump_ssh = None

#     def disconnect(self) -> None:
#         """Terminate both SSH sessions and stop the keep-alive thread."""
#         if hasattr(self, "_stop_keepalive"):
#             self._stop_keepalive.set()
#         if hasattr(self, "_keepalive_thread") and self._keepalive_thread:
#             self._keepalive_thread.join(timeout=1)

#         if hasattr(self, "_target_ssh") and self._target_ssh:
#             self._target_ssh.close()
#             self._target_ssh = None

#         if hasattr(self, "_jump_ssh") and self._jump_ssh:
#             self._jump_ssh.close()
#             self._jump_ssh = None

#     # ---------------------------------------------------------------------------- #
#     #                               Command execution                              #
#     # ---------------------------------------------------------------------------- #

#     def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
#         """Execute command and return structured result."""
#         if not self._target_ssh:
#             return ConnectionResult("", "Not connected - Call connect() first.", -1)

#         try:
#             _, stdout, stderr = self._target_ssh.exec_command(command, timeout=timeout)
#             stdout_str = stdout.read().decode()
#             stderr_str = stderr.read().decode()
#             return_code = stdout.channel.recv_exit_status()

#             return ConnectionResult(stdout_str, stderr_str, return_code)
#         except Exception as e:
#             logger.exception(f"Command execution failed: {command}")
#             return ConnectionResult("", f"Execution error: {e}", -1)

#     def exec_command(self, command: str, timeout: int | None = None) -> tuple[str, str]:
#         """Legacy method for backward compatibility."""
#         result = self.execute_command(command, timeout)
#         return result.stdout, result.stderr

#     # ---------------------------------------------------------------------------- #
#     #                               Connection status                              #
#     # ---------------------------------------------------------------------------- #

#     def is_connected(self) -> bool:
#         """Return True if target SSH transport is alive."""
#         if not self._target_ssh:
#             return False

#         transport = self._target_ssh.get_transport()
#         return transport is not None and transport.is_active()

"""Robust SSH connection with multi-jump support, lifecycle, and infinite keepalive."""

from collections.abc import Sequence
import logging
import threading
import time
from typing import Any

import paramiko

from src.core.lifecycle import ILifecycleAware
from src.interfaces.connection import ConnectionResult, IConnection, IConnectionFactory
from src.models.config import Host, Route

logger = logging.getLogger(__name__)


class SshConnection(IConnection, ILifecycleAware):
    """
    SSH connection manager with support for multiple jump hosts and keepalive.

    Features:
    - Direct or multi-hop SSH connections
    - Lifecycle management (initialize, cleanup)
    - Infinite keepalive
    - Execute commands with structured results
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        jump_hosts: Sequence[Host] | None = None,
        keepalive_interval: int = 30,
    ):
        """
        Args:
            host: Target host address
            username: Target username
            password: Target password (can use secrets)
            jump_hosts: Optional list of jump hosts (Host objects) in order
            keepalive_interval: Seconds between keepalive packets
        """
        self._host = host
        self._username = username
        self._password = password
        self._jump_hosts = jump_hosts or []
        self._keepalive_interval = keepalive_interval

        self._ssh_client: paramiko.SSHClient | None = None
        self._jump_clients: list[paramiko.SSHClient] = []
        self._keepalive_thread: threading.Thread | None = None
        self._stop_keepalive = threading.Event()

    @classmethod
    def from_config(cls, route: Route) -> "SshConnection":
        """Create SshConnection from Route object."""
        if not config.networks.routes:
            msg = "No routes defined in configuration"
            raise ValueError(msg)

        target = route.target

        return cls(
            host=target.ip,
            username=target.username,
            password=target.password.get_secret_value(),
            jump_hosts=route.jumps,
        )

    # -------------------- Lifecycle -------------------- #
    def initialize(self) -> None:
        self.connect()

    def cleanup(self) -> None:
        self.disconnect()

    def __enter__(self) -> "SshConnection":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()

    # -------------------- Connection Handling -------------------- #
    def connect(self) -> bool:
        """Connect to target host, optionally through multiple jump hosts."""
        try:
            if not self._jump_hosts:
                return self._connect_direct()
            return self._connect_via_jumps()
        except Exception:
            logger.exception("SSH connection failed")
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Terminate SSH sessions and stop keepalive."""
        self._stop_keepalive.set()
        if self._keepalive_thread:
            self._keepalive_thread.join(timeout=1)
            self._keepalive_thread = None

        if self._ssh_client:
            self._ssh_client.close()
            self._ssh_client = None

        for client in self._jump_clients:
            client.close()
        self._jump_clients.clear()

    def is_connected(self) -> bool:
        if not self._ssh_client:
            return False
        transport = self._ssh_client.get_transport()
        return transport is not None and transport.is_active()

    # -------------------- Command Execution -------------------- #ConnectionResult
    def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
        if not self.is_connected():
            return ConnectionResult("", "Not connected", -1)

        try:
            _, stdout, stderr = self._ssh_client.exec_command(command, timeout=timeout)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()
            return_code = stdout.channel.recv_exit_status()
            return ConnectionResult(stdout_str, stderr_str, return_code)
        except Exception as e:
            logger.exception(f"Command execution failed: {command}")
            return ConnectionResult("", f"Execution error: {e}", -1)

    def exec_command(self, command: str, timeout: int | None = None) -> tuple[str, str]:
        result = self.execute_command(command, timeout)
        return result.stdout, result.stderr

    # -------------------- Internal Connection -------------------- #
    def _create_ssh_client(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        return client

    def _connect_direct(self) -> bool:
        """Direct connection without jumps."""
        self._ssh_client = self._create_ssh_client()
        self._ssh_client.connect(
            hostname=self._host,
            username=self._username,
            password=self._password,
            look_for_keys=False,
            allow_agent=False,
        )
        self._start_keepalive()
        return True

    def _connect_via_jumps(self) -> bool:
        """Connect through multiple jump hosts."""
        previous_transport = None
        for i, jump in enumerate(self._jump_hosts):
            client = self._create_ssh_client()
            if previous_transport:
                # Connect via channel from previous jump
                channel = previous_transport.open_channel(
                    "direct-tcpip",
                    (jump.address, 22),
                    (self._jump_hosts[i - 1].address, 22),
                )
                client.connect(
                    hostname=jump.address,
                    username=jump.username,
                    password=jump.password.get_secret_value(),
                    sock=channel,
                    look_for_keys=False,
                    allow_agent=False,
                )
            else:
                # First jump host connects directly
                client.connect(
                    hostname=jump.address,
                    username=jump.username,
                    password=jump.password.get_secret_value(),
                    look_for_keys=False,
                    allow_agent=False,
                )
            self._jump_clients.append(client)
            previous_transport = client.get_transport()
            if not previous_transport:
                raise RuntimeError(f"Failed to get transport from jump host {jump.address}")
            previous_transport.set_keepalive(self._keepalive_interval)

        # Connect to final target through last jump
        self._ssh_client = self._create_ssh_client()
        last_jump_addr = self._jump_hosts[-1].address if self._jump_hosts else None
        channel = previous_transport.open_channel(
            "direct-tcpip",
            (self._host, 22),
            (last_jump_addr, 22) if last_jump_addr else ("127.0.0.1", 0),
        )
        self._ssh_client.connect(
            hostname=self._host,
            username=self._username,
            password=self._password,
            sock=channel,
            look_for_keys=False,
            allow_agent=False,
        )

        self._start_keepalive()
        return True

    # -------------------- Keepalive -------------------- #
    def _start_keepalive(self) -> None:
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def _keepalive_loop(self) -> None:
        """Send keepalive packets to all active transports."""
        while not self._stop_keepalive.is_set():
            try:
                # Keepalive for target
                if self._ssh_client:
                    transport = self._ssh_client.get_transport()
                    if transport and transport.is_active():
                        transport.send_ignore()

                # Keepalive for jumps
                for client in self._jump_clients:
                    transport = client.get_transport()
                    if transport and transport.is_active():
                        transport.send_ignore()
            except Exception:
                logger.exception("Keepalive failed")
            time.sleep(self._keepalive_interval)


class SshConnectionFactory(IConnectionFactory):
    """Factory to create multi-jump SSH connections from config."""

    def create_connection(self, config: Any) -> IConnection:
        host = getattr(config, "ip", "localhost")
        username = getattr(config, "username", "user")
        password = getattr(config, "password", "")

        if hasattr(password, "get_secret_value"):
            password = password.get_secret_value()

        jump_hosts = getattr(config, "jump_hosts", None)
        return SshConnection(host, username, password, jump_hosts)
