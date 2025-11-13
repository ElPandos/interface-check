"""Example usage of the diagnostic tools."""

from pathlib import Path

from src.core.connect import SshConnection
from src.platform.bak.commands import System
from src.platform.tools.tool_factory import ToolFactory


def main():
    """Example tool usage."""
    # Initialize SSH connection (you'll need proper config)
    _cfg = System()  # Load your config
    _ssh = SshConnection(_cfg)

    if not _ssh.connect():
        return

    try:
        # Create ethtool instance
        ethtool = ToolFactory.create_tool("ethtool", _ssh, "eth0")

        # Execute specific command
        result = ethtool.execute_command("info")
        if result.success:
            ethtool.parse_output("info", result.stdout)

        # Collect all data
        ethtool.collect_all()

        # Export data
        ethtool.export_data(Path("ethtool_data.json"))

        # Use other tools
        dmesg = ToolFactory.create_tool("dmesg", _ssh)
        network_logs = dmesg.execute_command("network")
        if network_logs.success:
            dmesg.parse_output("network", network_logs.stdout)

    finally:
        _ssh.disconnect()


if __name__ == "__main__":
    main()
