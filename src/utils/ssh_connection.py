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
        self.jump_host = app_config.hosts.jump_hosts[0].ip
        self.jump_user = app_config.hosts.jump_hosts[0].username
        self.jump_pass = app_config.hosts.jump_hosts[0].password

        self.target_host = app_config.hosts.target_host.ip
        self.target_user = app_config.hosts.target_host.username
        self.target_pass = app_config.hosts.target_host.password

        self.keepalive_interval = keepalive_interval

        self._jump_ssh: paramiko.SSHClient | None = None
        self._target_ssh: paramiko.SSHClient | None = None
        self._keepalive_thread: threading.Thread | None = None
        self._stop_keepalive = threading.Event()

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
        # Jump host transport
        if self._jump_ssh is None:
            return False
        jump_transport = self._jump_ssh.get_transport()
        if not (jump_transport and jump_transport.is_active()):
            return False

        # Target host transport
        if self._target_ssh is None:
            return False
        target_transport = self._target_ssh.get_transport()
        if not (target_transport and target_transport.is_active()):
            return False

        return True
