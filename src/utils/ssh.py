import json
from pathlib import Path
from typing import Any

import paramiko

# ----------------------------------------------------------------------
# Helper types
# ----------------------------------------------------------------------
HostInfo = tuple[str, str, str]  # (host, user, password)

# ----------------------------------------------------------------------
# Ssh class – added module‑level docstring
# ----------------------------------------------------------------------
"""
Utility for executing a command on a remote host via an arbitrary chain of
SSH jumphosts.  Connection details are read from a JSON file whose structure
matches the ``hosts`` key shown in the example below.

Example ``ssh_config.json``:

{
    "jumphosts": [
        "host_1": {
            "host":     "127.0.0.1",
            "user":     "user",
            "password": "pass"
            },
        "host_2": {
            "host":     "127.0.0.1",
            "user":     "user",
            "password": "pass"
            },

        ],
    "targethost": {
        "host":     "127.0.0.1",
        "user":     "user",
        "password": "pass"
  }
}
"""


class Ssh:
    """SSH helper that can tunnel through a list of jumphosts.

    The constructor takes the path to a JSON configuration file.  The file
    must contain two top‑level arrays: ``jumphosts`` (optional, ordered) and
    ``targets`` (exactly one entry for now).  Each entry is a mapping with the
    keys ``host``, ``user`` and ``pass``.
    """

    def __init__(self, config_path: str | Path) -> None:
        """Load connection data from *config_path*."""
        self.config = self._load_config(Path(config_path))
        # optional logger – replace with your own if needed
        self._log = self.debug  # alias used later in the file

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_config(path: Path) -> dict[str, Any]:
        """Read the JSON file and return the parsed dictionary."""
        if not path.is_file():
            raise FileNotFoundError(f"SSH config file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _to_hostinfo(entry: dict[str, str]) -> HostInfo:
        """Convert a JSON dict to a ``(host, user, password)`` tuple."""
        try:
            return entry["host"], entry["user"], entry["pass"]
        except KeyError as exc:
            raise ValueError(f"Missing required key {exc} in SSH config entry") from exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def exec(self, command: str) -> tuple[str, str]:
        """Execute *command* on the final target host.

        Returns a ``(stdout, stderr)`` tuple.
        """
        return self.__run_remote(command)

    # ------------------------------------------------------------------
    # Core implementation – now supports an arbitrary chain of jumphosts
    # ------------------------------------------------------------------
    def __run_remote(self, command: str) -> tuple[str, str]:
        """Build the SSH tunnel chain and run *command* on the target host.

        The method:
        1. Creates an SSH client for each jumphost in the order they appear.
        2. Opens a ``direct-tcpip`` channel from the previous hop to the next.
        3. Finally connects to the target host through the last channel.
        4. Executes *command* and returns its output.
        """
        # ------------------------------------------------------------------
        # Resolve configuration
        # ------------------------------------------------------------------
        jumphost_entries: list[dict[str, str]] = self.config.get("jumphosts", [])
        target_entries: list[dict[str, str]] = self.config.get("targets", [])

        if not target_entries:
            raise ValueError("SSH config must contain at least one target host")

        # Currently we support a single target; extend as needed.
        target_host, target_user, target_pass = self._to_hostinfo(target_entries[0])
        jumphosts: list[HostInfo] = [self._to_hostinfo(e) for e in jumphost_entries]

        # ------------------------------------------------------------------
        # Create the chain of SSH clients
        # ------------------------------------------------------------------
        # List of (client, transport) tuples; we keep the clients alive until
        # the command finishes, then close them in reverse order.
        clients: list[paramiko.SSHClient] = []

        try:
            # First hop – direct connection from the local machine
            prev_transport = None
            for idx, (j_host, j_user, j_pass) in enumerate(jumphosts):
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(
                    j_host,
                    username=j_user,
                    password=j_pass,
                    look_for_keys=False,
                    allow_agent=False,
                )
                clients.append(ssh)

                # Open a channel from the current hop to the next hop (or target)
                transport = ssh.get_transport()
                next_host = jumphosts[idx + 1][0] if idx + 1 < len(jumphosts) else target_host
                channel = transport.open_channel(
                    "direct-tcpip",
                    (next_host, 22),
                    (j_host, 22),
                )
                prev_transport = channel  # the next connect will use this as ``sock``

            # ------------------------------------------------------------------
            # Final connection (through the last channel, or directly if no jumps)
            # ------------------------------------------------------------------
            final_ssh = paramiko.SSHClient()
            final_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            final_ssh.connect(
                target_host,
                username=target_user,
                password=target_pass,
                sock=prev_transport,  # ``None`` works for a direct connection
                look_for_keys=False,
                allow_agent=False,
            )
            clients.append(final_ssh)

            # ------------------------------------------------------------------
            # Run the command
            # ------------------------------------------------------------------
            stdin, stdout, stderr = final_ssh.exec_command(command)
            stdout_str = stdout.read().decode()
            stderr_str = stderr.read().decode()

            self._log(f"Run remote - STDOUT: {stdout_str}")
            self._log(f"Run remote - STDERR: {stderr_str}")

            return stdout_str, stderr_str

        finally:
            # Close all SSH clients (target first, then jumphosts in reverse order)
            for client in reversed(clients):
                client.close()

    # ------------------------------------------------------------------
    # Simple logger – replace with your app’s logger if needed
    # ------------------------------------------------------------------
    @staticmethod
    def debug(msg: str) -> None:
        print(msg)  # or use ``logging.debug`` in a real project
