"""Tool factory for creating diagnostic tool instances."""

from typing import ClassVar

from src.core.connect import SshConnection
from src.interfaces.component import ITool
from src.platform.enums.software import ToolType
from src.platform.tools.dmesg import DmesgTool
from src.platform.tools.ethtool import EthtoolTool
from src.platform.tools.mlx import MlxTool
from src.platform.tools.mst import MstTool
from src.platform.tools.rdma import RdmaTool
from src.platform.tools.system import SystemTool


class ToolFactory:
    """Factory for creating diagnostic tool instances.

    Provides centralized tool creation with support for ethtool, mlx tools,
    mst, rdma, system utilities, and dmesg.
    """

    _TOOLS: ClassVar[dict[ToolType, type[ITool]]] = {
        ToolType.ETHTOOL: EthtoolTool,
        ToolType.MLX: MlxTool,
        ToolType.MST: MstTool,
        ToolType.RDMA: RdmaTool,
        ToolType.SYSTEM: SystemTool,
        ToolType.DMESG: DmesgTool,
    }

    @classmethod
    def create_tool(
        cls, tool_type: ToolType, ssh: SshConnection, interfaces: list[str] | None = None
    ) -> ITool:
        """Create a tool instance.

        Args:
            tool_type: Type of the tool to create
            ssh: SSH connection for command execution
            interfaces: Optional list of network interfaces

        Returns:
            ITool: Tool instance

        Raises:
            ValueError: If tool_type is not supported
        """
        if tool_type not in cls._TOOLS:
            available = ", ".join(cls._TOOLS.keys())
            raise ValueError(f"Unknown tool '{tool_type}'. Available: {available}")

        tool_class = cls._TOOLS[tool_type]
        return tool_class(ssh, interfaces)

    @classmethod
    def get_available_tools(cls) -> list[ToolType]:
        """Get list of available tool types.

        Returns:
            list[ToolType]: List of registered ToolType enums
        """
        return list(cls._TOOLS.keys())

    @classmethod
    def register_tool(cls, name: str, tool_class: type[ITool]) -> None:
        """Register a new tool class dynamically.

        Args:
            name: Tool name identifier
            tool_class: Tool class implementing ITool interface
        """
        cls._TOOLS[name] = tool_class
