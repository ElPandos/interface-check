"""Independent tool registry system."""

from abc import ABC, abstractmethod
import logging
from typing import Any

logger = logging.getLogger(__name__)


class Tool(ABC):
    """Abstract tool interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name identifier."""

    @abstractmethod
    def execute(self, command: str, **kwargs) -> Any:
        """Execute tool command."""

    @abstractmethod
    def get_commands(self) -> dict[str, str]:
        """Get available commands."""


class ToolRegistry:
    """Independent registry for managing tools."""

    def __init__(self):
        self._tools: dict[str, type[Tool]] = {}
        self._instances: dict[str, Tool] = {}

    def register(self, tool_class: type[Tool]) -> None:
        """Register a tool class."""
        # For adapter classes, we need to handle differently
        if hasattr(tool_class, "_tool_name"):
            name = tool_class._tool_name
        else:
            # Try to create instance to get name
            try:
                temp_instance = tool_class()
                name = temp_instance.name
            except Exception:
                # Fallback to class name
                name = tool_class.__name__.lower().replace("adapter", "").replace("tool", "")

        self._tools[name] = tool_class
        logger.debug(f"Registered tool: {name}")

    def register_instance(self, tool: Tool) -> None:
        """Register a tool instance directly."""
        name = tool.name
        self._tools[name] = type(tool)
        self._instances[name] = tool
        logger.debug(f"Registered tool instance: {name}")

    def create_tool(self, name: str, **kwargs) -> Tool:
        """Create tool instance."""
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Unknown tool '{name}'. Available: {available}")

        tool_class = self._tools[name]
        return tool_class(**kwargs)

    def get_tool(self, name: str, **kwargs) -> Tool:
        """Get or create cached tool instance."""
        # Check if we have a direct instance first
        if name in self._instances:
            return self._instances[name]

        cache_key = f"{name}_{hash(frozenset(kwargs.items()))}"

        if cache_key not in self._instances:
            self._instances[cache_key] = self.create_tool(name, **kwargs)

        return self._instances[cache_key]

    def get_available_tools(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self._tools.keys())

    def clear_cache(self) -> None:
        """Clear cached tool instances."""
        self._instances.clear()

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            # Remove cached instances
            to_remove = [key for key in self._instances if key.startswith(f"{name}_")]
            for key in to_remove:
                del self._instances[key]
            logger.debug(f"Unregistered tool: {name}")


# Global registry instance
_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry."""
    return _registry
