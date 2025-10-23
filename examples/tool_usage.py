"""Example usage of the diagnostic tools."""

from pathlib import Path

from src.core.connect import SshConnection
from src.tools.factory import ToolFactory


def main():
    """Example tool usage."""
    # Initialize SSH connection (you'll need proper config)
    app_config = System()  # Load your config
    self._ssh_connection = SshConnection(app_config)

    if not self._ssh.connect():
        return

    try:
        # Create ethtool instance
        ethtool = ToolFactory.create_tool("ethtool", self._ssh, "eth0")

        # Execute specific command
        result = ethtool.execute_command("info")
        if result.success:
            ethtool.parse_output("info", result.stdout)

        # Collect all data
        ethtool.collect_all()

        # Export data
        ethtool.export_data(Path("ethtool_data.json"))

        # Use other tools
        dmesg = ToolFactory.create_tool("dmesg", self._ssh)
        network_logs = dmesg.execute_command("network")
        if network_logs.success:
            dmesg.parse_output("network", network_logs.stdout)

    finally:
        self._ssh.disconnect()


if __name__ == "__main__":
    main()
