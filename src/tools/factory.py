"""Tool factory for creating diagnostic tool instances."""

from typing import ClassVar

from src.mixins.tool import Tool
from src.tools.dmesg import DmesgTool
from src.tools.ethtool import EthtoolTool
from src.tools.mlxconfig import MlxconfigTool
from src.utils.ssh_connection import SshConnection


class ToolFactory:
    """Factory for creating diagnostic tool instances."""

    _TOOLS: ClassVar[dict[str, type[Tool]]] = {
        "ethtool": EthtoolTool,
        "mlxconfig": MlxconfigTool,
        "dmesg": DmesgTool,
    }

    @classmethod
    def create_tool(cls, tool_name: str, ssh_connection: SshConnection, interface: str | None = None) -> Tool:
        """Create a tool instance.

        Args:
            tool_name: Name of the tool to create
            ssh_connection: SSH connection for command execution
            interface: Optional interface name

        Returns:
            Tool instance

        Raises:
            ValueError: If tool_name is not supported
        """
        if tool_name not in cls._TOOLS:
            available = ", ".join(cls._TOOLS.keys())
            raise ValueError(f"Unknown tool '{tool_name}'. Available: {available}")

        tool_class = cls._TOOLS[tool_name]
        return tool_class(ssh_connection, interface)

    @classmethod
    def get_available_tools(cls) -> list[str]:
        """Get list of available tool names."""
        return list(cls._TOOLS.keys())

    @classmethod
    def register_tool(cls, name: str, tool_class: type[Tool]) -> None:
        """Register a new tool class.

        Args:
            name: Tool name
            tool_class: Tool class implementing Tool interface
        """
        cls._TOOLS[name] = tool_class
