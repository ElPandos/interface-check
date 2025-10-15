# """SSH connection implementation."""

# import logging
# import threading
# import time
# from typing import Any

# import paramiko

# from src.core.lifecycle import ILifecycleAware
# from src.interfaces.connection import ConnectionResult, IConnection, IConnectionFactory

# logger = logging.getLogger(__name__)


# class SshConnection(IConnection, ILifecycleAware):
#     """SSH connection implementation with lifecycle management."""

#     def __init__(
#         self,
#         host: str,
#         username: str,
#         password: str,
#         jump_host: str | None = None,
#         jump_username: str | None = None,
#         jump_password: str | None = None,
#         keepalive_interval: int = 30,
#     ):
#         self._host = host
#         self._username = username
#         self._password = password
#         self._jump_host = jump_host
#         self._jump_username = jump_username
#         self._jump_password = jump_password
#         self._keepalive_interval = keepalive_interval

#         self._ssh_client: paramiko.SSHClient | None = None
#         self._jump_client: paramiko.SSHClient | None = None
#         self._keepalive_thread: threading.Thread | None = None
#         self._stop_keepalive = threading.Event()

#     def initialize(self) -> None:
#         """Initialize SSH connection."""
#         self.connect()

#     def cleanup(self) -> None:
#         """Clean up SSH connection."""
#         self.disconnect()

#     def connect(self) -> bool:
#         """Establish SSH connection."""
#         try:
#             if self._jump_host:
#                 return self._connect_with_jump()
#             return self._connect_direct()
#         except Exception:
#             logger.exception("SSH connection failed")
#             self.disconnect()
#             return False

#     def disconnect(self) -> None:
#         """Close SSH connection and cleanup."""
#         self._stop_keepalive.set()

#         if self._keepalive_thread:
#             self._keepalive_thread.join(timeout=1)
#             self._keepalive_thread = None

#         if self._ssh_client:
#             self._ssh_client.close()
#             self._ssh_client = None

#         if self._jump_client:
#             self._jump_client.close()
#             self._jump_client = None

#     def is_connected(self) -> bool:
#         """Check if SSH connection is active."""
#         if not self._ssh_client:
#             return False

#         transport = self._ssh_client.get_transport()
#         return transport is not None and transport.is_active()

#     def execute_command(self, command: str, timeout: int | None = None) -> ConnectionResult:
#         """Execute command over SSH."""
#         if not self.is_connected():
#             return ConnectionResult("", "Not connected", -1)

#         try:
#             _, stdout, stderr = self._ssh_client.exec_command(command, timeout=timeout)
#             stdout_str = stdout.read().decode()
#             stderr_str = stderr.read().decode()
#             return_code = stdout.channel.recv_exit_status()

#             return ConnectionResult(stdout_str, stderr_str, return_code)
#         except Exception as e:
#             logger.exception(f"Command execution failed: {command}")
#             return ConnectionResult("", f"Execution error: {e}", -1)

#     def _connect_direct(self) -> bool:
#         """Connect directly to target host."""
#         self._ssh_client = paramiko.SSHClient()
#         self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#         self._ssh_client.connect(
#             hostname=self._host,
#             username=self._username,
#             password=self._password,
#             look_for_keys=False,
#             allow_agent=False,
#         )

#         self._start_keepalive()
#         return True

#     def _connect_with_jump(self) -> bool:
#         """Connect through jump host."""
#         # Connect to jump host
#         self._jump_client = paramiko.SSHClient()
#         self._jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#         self._jump_client.connect(
#             hostname=self._jump_host,
#             username=self._jump_username,
#             password=self._jump_password,
#             look_for_keys=False,
#             allow_agent=False,
#         )

#         # Create tunnel to target
#         jump_transport = self._jump_client.get_transport()
#         if not jump_transport:
#             msg = "Failed to get transport from jump host"
#             raise RuntimeError(msg)

#         dest_addr = (self._host, 22)
#         local_addr = (self._jump_host, 22)
#         channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

#         # Connect to target through tunnel
#         self._ssh_client = paramiko.SSHClient()
#         self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#         self._ssh_client.connect(
#             hostname=self._host,
#             username=self._username,
#             password=self._password,
#             sock=channel,
#             look_for_keys=False,
#             allow_agent=False,
#         )

#         self._start_keepalive()
#         return True

#     def _start_keepalive(self) -> None:
#         """Start keepalive thread."""
#         self._stop_keepalive.clear()
#         self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
#         self._keepalive_thread.start()

#     def _keepalive_loop(self) -> None:
#         """Send keepalive packets."""
#         while not self._stop_keepalive.is_set():
#             try:
#                 if self._ssh_client:
#                     transport = self._ssh_client.get_transport()
#                     if transport and transport.is_active():
#                         transport.send_ignore()

#                 if self._jump_client:
#                     transport = self._jump_client.get_transport()
#                     if transport and transport.is_active():
#                         transport.send_ignore()
#             except Exception:
#                 logger.exception("Keepalive failed")

#             time.sleep(self._keepalive_interval)


# class SshConnectionFactory(IConnectionFactory):
#     """Factory for creating SSH connections."""

#     def create_connection(self, config: Any) -> IConnection:
#         """Create SSH connection from configuration."""
#         # Extract connection parameters from config
#         host = getattr(config, "ip", "localhost")
#         username = getattr(config, "username", "user")
#         password = getattr(config, "password", "")

#         if hasattr(password, "get_secret_value"):
#             password = password.get_secret_value()

#         return SshConnection(host, username, password)
