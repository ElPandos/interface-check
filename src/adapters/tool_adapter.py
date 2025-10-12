"""Adapter for existing tool implementations."""

from typing import Any

from src.core.tool_registry import Tool
from src.interfaces.connection import IConnection
from src.mixins.tool import Tool as LegacyTool


class LegacyToolAdapter(Tool):
    """Adapter to make legacy tools work with new registry."""

    def __init__(self, legacy_tool: LegacyTool):
        self._legacy_tool = legacy_tool

    @property
    def name(self) -> str:
        return self._legacy_tool.name

    def execute(self, command: str, **_kwargs) -> Any:
        result = self._legacy_tool.execute_command(command)
        if result.success:
            return self._legacy_tool.parse_output(command, result.stdout)
        return None

    def get_commands(self) -> dict[str, str]:
        return self._legacy_tool.available_commands()


class ConnectionToolAdapter(Tool):
    """Tool adapter that uses IConnection interface."""

    def __init__(self, connection: IConnection, tool_name: str, interface: str | None = None):
        self._connection = connection
        self._tool_name = tool_name
        self._interface = interface
        self._commands = self._get_tool_commands()

    @property
    def name(self) -> str:
        return self._tool_name

    def execute(self, command: str, **_kwargs) -> Any:
        if command not in self._commands:
            return None

        cmd_template = self._commands[command]
        if self._interface:
            cmd_template = cmd_template.format(interface=self._interface)

        result = self._connection.execute_command(cmd_template)
        if result.success:
            return self._parse_output(command, result.stdout)
        return None

    def get_commands(self) -> dict[str, str]:
        return self._commands.copy()

    def _get_tool_commands(self) -> dict[str, str]:
        """Get commands for specific tool."""
        if self._tool_name == "ethtool":
            return {
                "info": "ethtool {interface}",
                "statistics": "ethtool -S {interface}",
                "driver": "ethtool -i {interface}",
            }
        return {}

    def _parse_output(self, command: str, output: str) -> Any:
        """Parse command output."""
        if command in ["info", "driver"]:
            return self._parse_key_value(output)
        if command == "statistics":
            return self._parse_numeric_key_value(output)
        return output

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
        return result

    def _parse_numeric_key_value(self, output: str) -> dict[str, int]:
        """Parse numeric key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                try:
                    result[key.strip()] = int(value.strip())
                except ValueError:
                    result[key.strip()] = value.strip()
        return result
