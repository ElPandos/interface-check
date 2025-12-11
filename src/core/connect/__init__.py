"""Connection management package."""

from src.core.connect.local import LocalConnection
from src.core.connect.ssh import SshConnection, create_ssh_connection

__all__ = ["LocalConnection", "SshConnection", "create_ssh_connection"]
