from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "cables"
LABEL = "Cables"


class CableTab(BaseTab):
    ICON_NAME: str = "cable"

    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class CablePanel(BasePanel, MultiScreen):
    def __init__(
        self,
        *,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, CableTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._cable_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("Cables")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._cable_screens:
                self._cable_screens[screen_num] = CableContent(self._ssh_connection, self._host_handler, self._config)

            cable_content = self._cable_screens[screen_num]
            cable_content.build(screen_num)


class CableContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._scan_results: ui.column | None = None

    def build(self, screen_num: int) -> None:
        """Build cable interface for the screen."""
        # Connection selector
        if self._host_handler:
            Selector(
                getattr(self._host_handler, "_connect_route", {}),
                getattr(self._host_handler, "_routes", {}),
                lambda conn_id: self._on_connection_change(conn_id),
            ).build()

        # Cable controls
        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button("Scan Interfaces", icon="cable", on_click=self._scan_interfaces).classes(
                "bg-red-500 hover:bg-red-600 text-white"
            )

            ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Scan results area
        with ui.column().classes("w-full mt-4"):
            ui.label("Cable Scan Results").classes("text-lg font-bold")
            self._scan_results = ui.column().classes("w-full gap-2")
            with self._scan_results:
                ui.label("No interface scans performed yet").classes("text-gray-500 italic")

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id

    def _scan_interfaces(self) -> None:
        """Scan network interfaces."""
        if not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if not self._scan_results:
            return

        with self._scan_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label("Interface Scan Completed").classes("font-bold text-red-600")
                ui.label("Cable and interface information would appear here").classes("text-sm text-gray-600")

        ui.notify("Interface scan completed", color="positive")

    def _clear_results(self) -> None:
        """Clear scan results."""
        if self._scan_results:
            self._scan_results.clear()
            with self._scan_results:
                ui.label("No interface scans performed yet").classes("text-gray-500 italic")
        ui.notify("Results cleared", color="info")
