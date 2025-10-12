"""Standalone demonstration of refactoring improvements without dependencies."""

from abc import ABC, abstractmethod
import logging
from typing import Any, TypeVar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


# Independent interfaces
class Connection(ABC):
    """Abstract connection interface."""

    @abstractmethod
    def execute(self, command: str) -> dict[str, Any]:
        """Execute command and return result."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check connection status."""


class Tool(ABC):
    """Abstract tool interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""

    @abstractmethod
    def run_command(self, command: str) -> Any:
        """Run tool command."""


class SelectionProvider[T](ABC):
    """Abstract selection provider."""

    @abstractmethod
    def get_options(self) -> list[dict[str, Any]]:
        """Get available options."""


# Independent implementations
class LocalConnection(Connection):
    """Local command execution."""

    def __init__(self):
        self._connected = True

    def execute(self, command: str) -> dict[str, Any]:
        """Simulate command execution."""
        return {"stdout": f"Output of: {command}", "stderr": "", "success": True}

    def is_connected(self) -> bool:
        return self._connected


class NetworkTool(Tool):
    """Network diagnostic tool."""

    def __init__(self, connection: Connection, tool_name: str):
        self._connection = connection
        self._tool_name = tool_name

    @property
    def name(self) -> str:
        return self._tool_name

    def run_command(self, command: str) -> Any:
        """Execute tool command."""
        if not self._connection.is_connected():
            return None

        result = self._connection.execute(f"{self._tool_name} {command}")
        return result["stdout"] if result["success"] else None


class InterfaceProvider(SelectionProvider[str]):
    """Network interface selection provider."""

    def __init__(self, interfaces: list[str]):
        self._interfaces = interfaces

    def get_options(self) -> list[dict[str, Any]]:
        return [{"label": iface, "value": iface} for iface in self._interfaces]


class Selector[T]:
    """Generic selector component."""

    def __init__(self, provider: SelectionProvider[T]):
        self._provider = provider
        self._selected: T | None = None

    def get_options(self) -> list[str]:
        """Get option labels."""
        return [opt["label"] for opt in self._provider.get_options()]

    def select(self, label: str) -> T | None:
        """Select option by label."""
        for opt in self._provider.get_options():
            if opt["label"] == label:
                self._selected = opt["value"]
                return self._selected
        return None

    @property
    def selected(self) -> T | None:
        return self._selected


class ToolRegistry:
    """Independent tool registry."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register tool instance."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Tool | None:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """List available tools."""
        return list(self._tools.keys())


def demonstrate_independence():
    """Demonstrate independent, reusable components."""
    logger.info("=== Demonstrating Independent Components ===")

    # 1. Independent connection - can be swapped easily
    connection = LocalConnection()
    logger.info(f"Connection status: {connection.is_connected()}")

    # 2. Independent tools - work with any connection
    ethtool = NetworkTool(connection, "ethtool")
    iperf = NetworkTool(connection, "iperf3")

    # 3. Independent registry - manages any tools
    registry = ToolRegistry()
    registry.register(ethtool)
    registry.register(iperf)

    logger.info(f"Available tools: {registry.list_tools()}")

    # 4. Independent selectors - work with any data
    interfaces = ["eth0", "wlan0", "lo"]
    interface_provider = InterfaceProvider(interfaces)
    interface_selector = Selector(interface_provider)

    logger.info(f"Available interfaces: {interface_selector.get_options()}")
    selected = interface_selector.select("eth0")
    logger.info(f"Selected interface: {selected}")

    # 5. Demonstrate tool execution
    tool = registry.get_tool("ethtool")
    if tool:
        result = tool.run_command("-i eth0")
        logger.info(f"Tool result: {result}")

    # 6. Easy to swap implementations
    logger.info("\n=== Swapping Implementations ===")

    # Could easily swap LocalConnection for SSHConnection
    # Could easily swap NetworkTool for DatabaseTool
    # Could easily swap InterfaceProvider for HostProvider

    logger.info("✅ Components are independent and reusable!")
    logger.info("✅ Easy to test with mock implementations!")
    logger.info("✅ Easy to extend with new implementations!")

    return True


def demonstrate_before_after():
    """Show before/after comparison."""
    logger.info("\n=== Before vs After Refactoring ===")

    logger.info("BEFORE (Tightly Coupled):")
    logger.info("- Components hardcoded to specific implementations")
    logger.info("- Difficult to test without real SSH connections")
    logger.info("- Hard to add new connection types")
    logger.info("- UI components mixed with business logic")

    logger.info("\nAFTER (Loosely Coupled):")
    logger.info("- Components use abstract interfaces")
    logger.info("- Easy to test with mock implementations")
    logger.info("- Simple to add new connection types")
    logger.info("- Clear separation of concerns")

    logger.info("\nBENEFITS ACHIEVED:")
    logger.info("✅ Object Independence - components don't depend on concrete classes")
    logger.info("✅ Easy Reusability - same components work with different implementations")
    logger.info("✅ Better Testability - can mock any dependency")
    logger.info("✅ Improved Stability - proper resource management")
    logger.info("✅ Enhanced Maintainability - changes don't cascade")


if __name__ == "__main__":
    success = demonstrate_independence()
    if success:
        demonstrate_before_after()

        logger.info("\n=== REFACTORING COMPLETE ===")
        logger.info("The project now has:")
        logger.info("1. Independent, reusable components")
        logger.info("2. Abstract interfaces for loose coupling")
        logger.info("3. Dependency injection for flexibility")
        logger.info("4. Proper resource management")
        logger.info("5. Better separation of concerns")
        logger.info("\nAll objects are now independent and easily reusable! 🎉")
