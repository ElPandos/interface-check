import logging
import threading
import time

import paramiko

from src.models.configurations import AppConfig


class SshConnection:
    """
    Handles an SSH tunnel through a jumphost to a final target.
    - connect()   : establishes both jump and target sessions.
    - disconnect(): cleanly closes both sessions.
    - exec_command(cmd): runs a command on the target host.
    A background thread sends a keep‑alive packet every 30 seconds so the
    connections stay open forever (or until you call disconnect()).
    """

    def __init__(self, app_config: AppConfig, keepalive_interval: int = 30):
        jump_host_config = app_config.hosts.jump_hosts[0]
        self.jump_host = jump_host_config.ip
        self.jump_user = jump_host_config.username
        self.jump_pass = jump_host_config.password

        target_config = app_config.hosts.target_host
        self.target_host = target_config.ip
        self.target_user = target_config.username
        self.target_pass = target_config.password

        self.keepalive_interval = keepalive_interval

        self._jump_ssh: paramiko.SSHClient | None = None
        self._target_ssh: paramiko.SSHClient | None = None

        self._keepalive_thread: threading.Thread | None = None
        self._stop_keepalive = threading.Event()

    def __del__(self) -> None:
        """Cleanup on garbage collection."""
        self.disconnect()

    def __enter__(self) -> "SshConnection":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - ensures cleanup."""
        self.disconnect()

    # ---------------------------------------------------------------------------- #
    #                              Connection handling                             #
    # ---------------------------------------------------------------------------- #

    def connect(self) -> None:
        """Open SSH sessions to the jumphost and then to the target via a tunnel."""
        # --------------------------------- Jump host -------------------------------- #
        try:
            self._jump_ssh = paramiko.SSHClient()
            self._jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._jump_ssh.connect(
                hostname=self.jump_host,
                username=self.jump_user,
                password=self.jump_pass,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException as e:
            raise RuntimeError(f"Authentication to target {self.jump_host} failed: {e}")

        # ----------------------------- Channel to target ---------------------------- #

        jump_transport = self._jump_ssh.get_transport()
        if not jump_transport:
            raise RuntimeError("Failed to get transport from jump host.")

        logging.info(f"Send keep alive packets every: {self.keepalive_interval} sec.")
        jump_transport.set_keepalive(self.keepalive_interval)
        dest_addr = (self.target_host, 22)
        local_addr = (self.jump_host, 22)
        channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        # -------------------------------- Target host ------------------------------- #

        try:
            self._target_ssh = paramiko.SSHClient()
            self._target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._target_ssh.connect(
                hostname=self.target_host,
                username=self.target_user,
                password=self.target_pass,
                sock=channel,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException as e:
            raise RuntimeError(f"Authentication to target {self.target_host} failed: {e}")

        # -------------------------- Start keep‑alive thread ------------------------- #
        self._stop_keepalive.clear()
        self._keepalive_thread = threading.Thread(target=self._keepalive_loop, daemon=True)
        self._keepalive_thread.start()

    def disconnect(self) -> None:
        """Terminate both SSH sessions and stop the keep‑alive thread."""
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

    def exec_command(self, command: str, timeout: int | None = None) -> tuple[str, str]:
        if not self._target_ssh:
            raise RuntimeError("Not connected – Call connect() first.")

        _, stdout, stderr = self._target_ssh.exec_command(command, timeout=timeout)

        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()

        return stdout_str, stderr_str

    # ---------------------------------------------------------------------------- #
    #                           Internal keep‑alive logic                          #
    # ---------------------------------------------------------------------------- #

    def _keepalive_loop(self) -> None:
        """Send a keep‑alive packet on each transport every *keepalive_interval* seconds."""
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
    #                               Connection status                              #
    # ---------------------------------------------------------------------------- #

    def is_connected(self) -> bool:
        """
        Return True if both the jump‑host and target SSH transports are alive.
        """
        return (
            self._jump_ssh is not None
            and self._jump_ssh.get_transport() is not None
            and self._jump_ssh.get_transport().is_active()
            and self._target_ssh is not None
            and self._target_ssh.get_transport() is not None
            and self._target_ssh.get_transport().is_active()
        )
