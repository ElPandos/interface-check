"""Network diagnostic tool implementations."""

import logging
import time
from typing import Any

from src.interfaces.connection import IConnection
from src.interfaces.tool import ITool, IToolFactory, ToolResult

logger = logging.getLogger(__name__)


class NetworkTool(ITool):
    """Base class for network diagnostic tools."""

    def __init__(self, connection: IConnection, interface: str | None = None):
        self._connection = connection
        self._interface = interface

    def execute(self, command: str, **_kwargs) -> ToolResult:
        """Execute tool command."""
        commands = self.get_commands()
        if command not in commands:
            return ToolResult(command=command, data=None, success=False, error=f"Unknown command: {command}")

        cmd_template = commands[command]
        if self._interface:
            cmd_template = cmd_template.format(interface=self._interface)

        start_time = time.perf_counter()
        result = self._connection.execute_command(cmd_template)
        execution_time = time.perf_counter() - start_time

        if result.success:
            try:
                parsed_data = self.parse_output(command, result.stdout)
                return ToolResult(command=cmd_template, data=parsed_data, success=True, execution_time=execution_time)
            except Exception as e:
                logger.exception(f"Failed to parse output for {command}")
                return ToolResult(
                    command=cmd_template,
                    data=None,
                    success=False,
                    error=f"Parse error: {e}",
                    execution_time=execution_time,
                )
        else:
            return ToolResult(
                command=cmd_template, data=None, success=False, error=result.stderr, execution_time=execution_time
            )


class EthtoolImpl(NetworkTool):
    """Ethtool implementation."""

    @property
    def name(self) -> str:
        return "ethtool"

    def get_commands(self) -> dict[str, str]:
        return {
            "info": "ethtool {interface}",
            "statistics": "ethtool -S {interface}",
            "driver": "ethtool -i {interface}",
            "module": "ethtool -m {interface}",
            "features": "ethtool -k {interface}",
            "ring": "ethtool -g {interface}",
            "coalesce": "ethtool -c {interface}",
        }

    def parse_output(self, command: str, output: str) -> Any:
        """Parse ethtool output."""
        if command == "info":
            return self._parse_key_value(output)
        if command == "statistics":
            return self._parse_numeric_key_value(output)
        if command == "features":
            return self._parse_features(output)
        return self._parse_key_value(output)

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

    def _parse_features(self, output: str) -> dict[str, bool]:
        """Parse features output."""
        result = {}
        for line in output.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().lower() == "on"
        return result


class MlxconfigImpl(NetworkTool):
    """Mlxconfig implementation."""

    @property
    def name(self) -> str:
        return "mlxconfig"

    def get_commands(self) -> dict[str, str]:
        return {
            "query": "mlxconfig -d {interface} q",
            "backup": "mlxconfig -d {interface} backup",
        }

    def parse_output(self, _command: str, output: str) -> Any:
        """Parse mlxconfig output."""
        return self._parse_key_value(output)

    def _parse_key_value(self, output: str) -> dict[str, str]:
        """Parse key-value output."""
        result = {}
        for line in output.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
        return result


class NetworkToolFactory(IToolFactory):
    """Factory for creating network diagnostic tools."""

    def __init__(self, connection: IConnection):
        self._connection = connection
        self._tools = {
            "ethtool": EthtoolImpl,
            "mlxconfig": MlxconfigImpl,
        }

    def create_tool(self, tool_name: str, **kwargs) -> ITool:
        """Create tool instance."""
        if tool_name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")

        tool_class = self._tools[tool_name]
        interface = kwargs.get("interface")
        return tool_class(self._connection, interface)

    def get_available_tools(self) -> list[str]:
        """Get list of available tools."""
        return list(self._tools.keys())
