"""Tool factory for creating diagnostic tool instances."""

from typing import ClassVar

from src.core.connect import SshConnection
from src.interfaces.tool import ITool
from src.platform.enums.software import ToolType
from src.platform.tools.ethtool import EthtoolTool
from src.platform.tools.mlx import MlxTool
from src.platform.tools.mst import MstTool
from src.platform.tools.rdma import RdmaTool
from src.platform.tools.system import SystemTool


class ToolFactory:
    """Factory for creating log/diagnostic tool instances."""

    _TOOLS: ClassVar[dict[ToolType, type[ITool]]] = {
        ToolType.ETHTOOL: EthtoolTool,
        ToolType.MLX: MlxTool,
        ToolType.MST: MstTool,
        ToolType.RDMA: RdmaTool,
        ToolType.SYSTEM: SystemTool,
    }

    @classmethod
    def create_tool(
        cls, tool_type: ToolType, ssh_connection: SshConnection, interfaces: list[str] | None = None
    ) -> ITool:
        """Create a tool instance.

        Args:
            tool_type: Type of the tool to create
            ssh_connection: SSH connection for command execution
            interface: Optional interface name

        Returns:
            Tool instance

        Raises:
            ValueError: If tool_type is not supported
        """
        if tool_type not in cls._TOOLS:
            available = ", ".join(cls._TOOLS.keys())
            raise ValueError(f"Unknown tool '{tool_type}'. Available: {available}")

        tool_class = cls._TOOLS[tool_type]
        return tool_class(ssh_connection, interfaces)

    @classmethod
    def get_available_tools(cls) -> list[ToolType]:
        """Get list of available tool types."""
        return list(cls._TOOLS.keys())

    @classmethod
    def register_tool(cls, name: str, tool_class: type[ITool]) -> None:
        """Register a new tool class.

        Args:
            name: Tool name
            tool_class: Tool class implementing Tool interface
        """
        cls._TOOLS[name] = tool_class
