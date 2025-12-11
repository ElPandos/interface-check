"""SSH and local connection management."""

from src.core.connect.local import LocalConnection
from src.core.connect.ssh import SshConnection
from src.core.enums.connect import HostType
from src.models.config import Host

__all__ = ["LocalConnection", "SshConnection", "create_ssh_connection"]


def create_ssh_connection(cfg, host_type: HostType) -> SshConnection:
    """Create SSH connection with jump host.

    Args:
        cfg: Configuration object
        host_type: Target host type (SLX or SUT)

    Returns:
        SshConnection: Configured SSH connection
    """
    jump_host = Host(
        ip=cfg.jump_host,
        username=cfg.jump_user,
        password=cfg.jump_pass,
    )

    if host_type == HostType.SLX:
        return SshConnection(
            host=cfg.slx_host,
            username=cfg.slx_user,
            password=cfg.slx_pass,
            jump_hosts=[jump_host],
        )
    return SshConnection(
        host=cfg.sut_host,
        username=cfg.sut_user,
        password=cfg.sut_pass,
        jump_hosts=[jump_host],
        sudo_pass=cfg.sut_sudo_pass,
    )
