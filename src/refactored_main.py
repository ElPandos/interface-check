"""Minimal refactored main demonstrating independent components."""

import logging

from src.adapters.collector_adapter import InterfaceDataSource
from src.adapters.tool_adapter import ConnectionToolAdapter
from src.core.data_collector import CollectorManager, DataCollector
from src.core.tool_registry import get_tool_registry
from src.implementations.local_connection import LocalConnection
from src.ui.components.selector import InterfaceSelectionProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demonstrate_independent_components():
    """Demonstrate how components work independently."""
    # 1. Independent connection (can be SSH, local, etc.)
    connection = LocalConnection()
    connection.connect()

    # 2. Independent tool registry
    registry = get_tool_registry()

    # Register tools dynamically
    ethtool = ConnectionToolAdapter(connection, "ethtool", "lo")
    registry.register_instance(ethtool)

    # 3. Independent data collection
    collector_manager = CollectorManager()

    # Add interface data collector
    interface_source = InterfaceDataSource(connection, "lo")
    interface_collector = DataCollector(interface_source, interval=2.0)
    collector_manager.add_collector("lo_stats", interface_collector)

    # 4. Independent UI components
    interfaces = ["lo", "eth0", "wlan0"]
    InterfaceSelectionProvider(interfaces)

    def on_interface_selected(interface):
        logger.info(f"Selected interface: {interface}")

    # This would be used in actual UI
    # selector = Selector(interface_provider, on_interface_selected, "Network Interface")

    # 5. Demonstrate tool execution
    try:
        tool = registry.get_tool("ethtool")
        result = tool.execute("info")
        logger.info(f"Tool result: {result}")
    except Exception as e:
        logger.info(f"Tool execution (expected on some systems): {e}")

    # 6. Demonstrate data collection
    collector_manager.start_all()

    import time

    time.sleep(3)  # Collect some data

    collector = collector_manager.get_collector("lo_stats")
    if collector:
        samples = collector.get_samples()
        logger.info(f"Collected {len(samples)} samples")
        if samples:
            logger.info(f"Latest sample: {samples[-1].data}")

    collector_manager.stop_all()
    connection.disconnect()

    logger.info("✅ All components worked independently!")


if __name__ == "__main__":
    demonstrate_independent_components()
