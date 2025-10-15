"""Refactored Ethtool panel with dependency injection."""

import logging

from nicegui import ui

from src.interfaces.configuration import IConfigurationProvider
from src.interfaces.connection import IConnection
from src.interfaces.tool import IToolFactory
from src.interfaces.ui import IEventBus
from src.ui.base.components import ToolPanel

logger = logging.getLogger(__name__)


class EthtoolPanel(ToolPanel):
    """Ethtool panel with dependency injection."""

    def __init__(
        self,
        config: IConfigurationProvider | None = None,
        connection: IConnection | None = None,
        tool_factory: IToolFactory | None = None,
        event_bus: IEventBus | None = None,
    ):
        super().__init__("ethtool", "Ethtool", "home_repair_service", config, connection, event_bus)
        self._tool_factory = tool_factory
        self._selected_interface: str | None = None
        self._available_interfaces: list[str] = []

    def _build_content(self) -> None:
        """Build ethtool panel content."""
        self._build_interface_selector()
        super()._build_content()

    def _build_interface_selector(self) -> None:
        """Build interface selection controls."""
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.label("Interface Selection").classes("text-lg font-bold")

            interface_select = ui.select(
                self._available_interfaces, value=self._selected_interface, label="Network Interface"
            ).classes("w-48")

            interface_select.on_value_change(self._on_interface_change)

            ui.button("Scan Interfaces", on_click=self._scan_interfaces, icon="search")

    def _scan_interfaces(self) -> None:
        """Scan for available network interfaces."""
        if not self._connection or not self._connection.is_connected():
            ui.notify("No connection available", type="warning")
            return

        try:
            # Get network interfaces using a simple command
            result = self._connection.execute_command("ls /sys/class/net/")
            if result.success:
                interfaces = [iface.strip() for iface in result.stdout.split() if iface.strip()]
                self._available_interfaces = [iface for iface in interfaces if iface != "lo"]  # Exclude loopback
                ui.notify(f"Found {len(self._available_interfaces)} interfaces", type="positive")

                # Refresh the interface selector
                self.refresh()
            else:
                ui.notify(f"Failed to scan interfaces: {result.stderr}", type="negative")
        except Exception as e:
            logger.exception("Interface scan failed")
            ui.notify(f"Interface scan failed: {e}", type="negative")

    def _on_interface_change(self, e) -> None:
        """Handle interface selection change."""
        self._selected_interface = e.value
        if self._selected_interface:
            ui.notify(f"Selected interface: {self._selected_interface}", type="info")

    def _execute_tool_commands(self) -> None:
        """Execute ethtool commands."""
        if not self._tool_factory or not self._selected_interface:
            return

        try:
            ethtool = self._tool_factory.create_tool("ethtool", interface=self._selected_interface)

            # Execute common ethtool commands
            commands = ["info", "statistics", "driver"]
            self._tool_results = {}

            for cmd in commands:
                try:
                    result = ethtool.execute(cmd)
                    if result.success:
                        self._tool_results[cmd] = result.data
                    else:
                        self._tool_results[cmd] = {"error": result.error}
                except Exception as e:
                    logger.exception(f"Failed to execute {cmd}")
                    self._tool_results[cmd] = {"error": str(e)}

            ui.notify(f"Executed {len(commands)} ethtool commands", type="positive")

        except Exception as e:
            logger.exception("Tool execution failed")
            ui.notify(f"Tool execution failed: {e}", type="negative")
