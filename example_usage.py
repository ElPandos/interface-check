"""Example demonstrating the improved architecture and independence."""

import logging
from pathlib import Path

from src.core.container import get_container
from src.core.event_bus import EventBus
from src.core.lifecycle import LifecycleManager
from src.implementations.json_config import JsonConfigurationFactory
from src.implementations.local_connection import LocalConnectionFactory
from src.implementations.network_tools import NetworkToolFactory
from src.interfaces.configuration import IConfigurationProvider
from src.interfaces.connection import IConnection
from src.interfaces.tool import IToolFactory
from src.interfaces.ui import IEventBus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demonstrate_dependency_injection():
    """Demonstrate how dependency injection makes components independent."""
    # Setup container
    container = get_container()
    lifecycle = LifecycleManager()

    # Register dependencies
    config_factory = JsonConfigurationFactory()
    config_provider = config_factory.create_provider("/tmp/demo_config.json")

    container.register_instance(IConfigurationProvider, config_provider)
    container.register_instance(IEventBus, EventBus())

    # Use LOCAL connection instead of SSH - no code changes needed!
    local_factory = LocalConnectionFactory()
    local_connection = local_factory.create_connection()

    container.register_instance(IConnection, local_connection)
    lifecycle.register(local_connection)

    # Create tool factory with local connection
    tool_factory = NetworkToolFactory(local_connection)
    container.register_instance(IToolFactory, tool_factory)

    # Now components can use any connection type transparently
    with lifecycle.managed_lifecycle():
        connection = container.get(IConnection)

        # Execute a local command
        connection.execute_command("echo 'Hello from local connection!'")


def demonstrate_tool_independence():
    """Demonstrate how tools are independent of connection type."""
    # Create local connection
    local_conn = LocalConnectionFactory().create_connection()
    local_conn.connect()

    # Create tool factory
    tool_factory = NetworkToolFactory(local_conn)

    # Tools work with any connection type
    try:
        # This would work the same with SSH connection
        ethtool = tool_factory.create_tool("ethtool", interface="lo")

        # Execute a command (will fail on most systems but demonstrates the pattern)
        ethtool.execute("info")

    except Exception:
        pass

    local_conn.disconnect()


def demonstrate_event_system():
    """Demonstrate decoupled event communication."""
    event_bus = EventBus()

    # Define event handlers
    def on_connection_change(data):
        pass

    def on_tool_result(data):
        pass

    # Subscribe to events
    event_bus.subscribe("connection_changed", on_connection_change)
    event_bus.subscribe("tool_result", on_tool_result)

    # Publish events (components don't need to know about each other)
    event_bus.publish("connection_changed", {"status": "connected", "type": "local"})
    event_bus.publish("tool_result", {"tool": "ethtool", "success": True})

    # Clean up
    event_bus.clear()


def demonstrate_configuration_flexibility():
    """Demonstrate flexible configuration management."""
    # Create temporary config file
    config_path = Path("/tmp/demo_config.json")

    # JSON configuration provider
    json_factory = JsonConfigurationFactory()
    json_provider = json_factory.create_provider(str(config_path))

    # Set some configuration
    json_provider.set("app.name", "Interface Check")
    json_provider.set("app.version", "2.0.0")
    json_provider.set("connection.type", "local")
    json_provider.set("connection.timeout", 30)

    # Save configuration
    json_provider.save()

    # Read configuration

    # Get entire section
    json_provider.get_section("app")

    # Clean up
    config_path.unlink(missing_ok=True)


if __name__ == "__main__":
    demonstrate_dependency_injection()
    demonstrate_tool_independence()
    demonstrate_event_system()
    demonstrate_configuration_flexibility()
