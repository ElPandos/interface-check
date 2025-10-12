"""System information panel demonstrating new architecture."""

import logging
from typing import Any

from nicegui import ui

from src.interfaces.configuration import IConfigurationProvider
from src.interfaces.connection import IConnection
from src.interfaces.ui import IEventBus
from src.ui.base.components import Panel

logger = logging.getLogger(__name__)


class SystemPanel(Panel):
    """System information panel with dependency injection."""

    def __init__(
        self,
        config: IConfigurationProvider | None = None,
        connection: IConnection | None = None,
        event_bus: IEventBus | None = None,
    ):
        super().__init__("system", "System Info", "computer", config, connection, event_bus)
        self._system_info: dict[str, Any] = {}

    def _build_content(self) -> None:
        """Build system panel content."""
        self._build_controls()
        self._build_system_info()

    def _build_controls(self) -> None:
        """Build system control interface."""
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.label("System Information").classes("text-lg font-bold")
            ui.space()

            connection_status = (
                "Connected" if (self._connection and self._connection.is_connected()) else "Disconnected"
            )
            color = "positive" if connection_status == "Connected" else "negative"
            ui.badge(connection_status, color=color)

            ui.button("Refresh", on_click=self._refresh_system_info, icon="refresh")
            ui.button("Export", on_click=self._export_info, icon="download")

    def _build_system_info(self) -> None:
        """Build system information display."""
        if self._system_info:
            with ui.card().classes("w-full"):
                ui.label("System Information").classes("text-lg font-bold mb-4")

                # Create tabs for different info categories
                with ui.tabs() as info_tabs:
                    ui.tab("general", "General", icon="info")
                    ui.tab("hardware", "Hardware", icon="memory")
                    ui.tab("network", "Network", icon="network_check")

                with ui.tab_panels(info_tabs, value="general"):
                    with ui.tab_panel("general"):
                        self._build_general_info()

                    with ui.tab_panel("hardware"):
                        self._build_hardware_info()

                    with ui.tab_panel("network"):
                        self._build_network_info()
        else:
            ui.label("No system information available. Click Refresh to load data.").classes("text-gray-500")

    def _build_general_info(self) -> None:
        """Build general system information."""
        general_info = self._system_info.get("general", {})

        with ui.grid(columns=2).classes("w-full gap-4"):
            for key, value in general_info.items():
                ui.label(f"{key}:").classes("font-semibold")
                ui.label(str(value))

    def _build_hardware_info(self) -> None:
        """Build hardware information."""
        hardware_info = self._system_info.get("hardware", {})

        if hardware_info:
            with ui.expansion("CPU Information", icon="processor"):
                ui.json_editor({"content": {"json": hardware_info.get("cpu", {})}}).run_editor_method(
                    "updateProps", {"readOnly": True}
                )

            with ui.expansion("Memory Information", icon="memory"):
                ui.json_editor({"content": {"json": hardware_info.get("memory", {})}}).run_editor_method(
                    "updateProps", {"readOnly": True}
                )
        else:
            ui.label("No hardware information available")

    def _build_network_info(self) -> None:
        """Build network information."""
        network_info = self._system_info.get("network", {})

        if network_info:
            with ui.expansion("Network Interfaces", icon="network_check"):
                ui.json_editor({"content": {"json": network_info}}).run_editor_method("updateProps", {"readOnly": True})
        else:
            ui.label("No network information available")

    def _refresh_system_info(self) -> None:
        """Refresh system information."""
        if not self._connection or not self._connection.is_connected():
            ui.notify("No connection available", type="warning")
            return

        try:
            self._system_info = {}

            # Collect general system information
            general_info = {}

            # Get hostname
            result = self._connection.execute_command("hostname")
            if result.success:
                general_info["hostname"] = result.stdout.strip()

            # Get uptime
            result = self._connection.execute_command("uptime")
            if result.success:
                general_info["uptime"] = result.stdout.strip()

            # Get OS information
            result = self._connection.execute_command("uname -a")
            if result.success:
                general_info["os_info"] = result.stdout.strip()

            self._system_info["general"] = general_info

            # Collect hardware information
            hardware_info = {}

            # Get CPU info
            result = self._connection.execute_command("lscpu")
            if result.success:
                cpu_info = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        cpu_info[key.strip()] = value.strip()
                hardware_info["cpu"] = cpu_info

            # Get memory info
            result = self._connection.execute_command("free -h")
            if result.success:
                hardware_info["memory"] = {"free_output": result.stdout}

            self._system_info["hardware"] = hardware_info

            # Collect network information
            result = self._connection.execute_command("ip addr show")
            if result.success:
                self._system_info["network"] = {"interfaces": result.stdout}

            ui.notify("System information refreshed", type="positive")
            self.refresh()

            # Publish event for other components
            if self._event_bus:
                self._event_bus.publish("system_info_updated", self._system_info)

        except Exception as e:
            logger.exception("Failed to refresh system information")
            ui.notify(f"Failed to refresh system info: {e}", type="negative")

    def _export_info(self) -> None:
        """Export system information."""
        if not self._system_info:
            ui.notify("No data to export", type="warning")
            return

        try:
            from datetime import datetime
            import json

            # Add timestamp to export
            export_data = {"timestamp": datetime.now().isoformat(), "system_info": self._system_info}

            # In a real implementation, this would save to file or provide download
            ui.notify("System information exported (demo)", type="positive")
            logger.info(f"System info export: {json.dumps(export_data, indent=2)}")

        except Exception as e:
            logger.exception("Failed to export system information")
            ui.notify(f"Export failed: {e}", type="negative")
