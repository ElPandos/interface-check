from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "toolbox"
LABEL = "Toolbox"


class ToolboxTab(BaseTab):
    ICON_NAME: str = "home_repair_service"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class ToolboxPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ) -> None:
        BasePanel.__init__(self, NAME, LABEL, ToolboxTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._toolbox_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base(LABEL)
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._toolbox_screens:
                self._toolbox_screens[screen_num] = ToolboxContent(
                    self._ssh_connection, self._host_handler, self._config
                )

            toolbox_content = self._toolbox_screens[screen_num]
            toolbox_content.build(screen_num)


class ToolboxContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._tool_results: ui.column | None = None

    def build(self, screen_num: int) -> None:
        """Build toolbox interface for the screen."""
        # Connection selector
        if self._host_handler:
            Selector(
                getattr(self._host_handler, "_connect_route", {}),
                getattr(self._host_handler, "_routes", {}),
                lambda conn_id: self._on_connection_change(conn_id),
            ).build()

        # Toolbox controls
        with ui.row().classes("w-full gap-2 mt-2 flex-wrap"):
            ui.button("Scan Interfaces", icon="search", on_click=self._scan_interfaces).classes(
                "bg-red-500 hover:bg-red-600 text-white"
            )

            ui.button("Network Tools", icon="build", on_click=self._network_tools).classes(
                "bg-blue-500 hover:bg-blue-600 text-white"
            )

            ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Tool results area
        with ui.column().classes("w-full mt-4"):
            ui.label("Toolbox Results").classes("text-lg font-bold")
            self._tool_results = ui.column().classes("w-full gap-2")
            with self._tool_results:
                ui.label("No tools executed yet").classes("text-gray-500 italic")

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id

    def _scan_interfaces(self) -> None:
        """Scan network interfaces."""
        if not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if not self._tool_results:
            return

        with self._tool_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label("Interface Scan Completed").classes("font-bold text-red-600")
                ui.label("Network interface information would appear here").classes("text-sm text-gray-600")

        ui.notify("Interface scan completed", color="positive")

    def _network_tools(self) -> None:
        """Run network tools."""
        if not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if not self._tool_results:
            return

        with self._tool_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label("Network Tools Executed").classes("font-bold text-blue-600")
                ui.label("Network diagnostic tools results would appear here").classes("text-sm text-gray-600")

        ui.notify("Network tools completed", color="positive")

    def _clear_results(self) -> None:
        """Clear tool results."""
        if self._tool_results:
            self._tool_results.clear()
            with self._tool_results:
                ui.label("No tools executed yet").classes("text-gray-500 italic")
        ui.notify("Results cleared", color="info")
