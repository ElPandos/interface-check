"""Example usage of the diagnostic tools."""

from pathlib import Path
from src.tools.factory import ToolFactory
from src.utils.ssh_connection import SshConnection
from src.models.configurations import AppConfig


def main():
    """Example tool usage."""
    # Initialize SSH connection (you'll need proper config)
    app_config = AppConfig()  # Load your config
    ssh_connection = SshConnection(app_config)

    if not ssh_connection.connect():
        print("Failed to connect via SSH")
        return

    try:
        # Create ethtool instance
        ethtool = ToolFactory.create_tool("ethtool", ssh_connection, "eth0")

        # Execute specific command
        result = ethtool.execute_command("info")
        if result.success:
            parsed_data = ethtool.parse_output("info", result.stdout)
            print(f"Interface info: {parsed_data}")

        # Collect all data
        all_data = ethtool.collect_all()
        print(f"All ethtool data: {all_data}")

        # Export data
        ethtool.export_data(Path("ethtool_data.json"))

        # Use other tools
        dmesg = ToolFactory.create_tool("dmesg", ssh_connection)
        network_logs = dmesg.execute_command("network")
        if network_logs.success:
            entries = dmesg.parse_output("network", network_logs.stdout)
            print(f"Found {len(entries)} network-related log entries")

    finally:
        ssh_connection.disconnect()


if __name__ == "__main__":
    main()
