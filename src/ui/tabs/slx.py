from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "slx"
LABEL = "SLX"


class SlxTab(BaseTab):
    ICON_NAME: str = "router"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class SlxPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, SlxTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._slx_screens: dict[int, Any] = {}

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
            if screen_num not in self._slx_screens:
                self._slx_screens[screen_num] = SlxContent(self._ssh_connection, self._host_handler, self._config)

            slx_content = self._slx_screens[screen_num]
            slx_content.build(screen_num)


class SlxContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._slx_results: ui.column | None = None
        self._buttons: dict[str, ui.button] = {}

    def build(self, screen_num: int) -> None:
        """Build SLX interface for the screen."""
        # Connection selector
        if self._host_handler:
            Selector(
                getattr(self._host_handler, "_connect_route", {}),
                getattr(self._host_handler, "_routes", {}),
                self._on_connection_change,
            ).build()

        # SLX controls
        with ui.row().classes("w-full gap-2 mt-2"):
            self._buttons["scan"] = ui.button("Scan Interfaces", icon="router", on_click=self._scan_interfaces).classes(
                "bg-red-500 hover:bg-red-600 text-white"
            )

            self._buttons["clear"] = ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # SLX results area
        with ui.column().classes("w-full mt-4"):
            ui.label("SLX Results").classes("text-lg font-bold")
            self._slx_results = ui.column().classes("w-full gap-2")
            self._show_empty_state()

        self._update_button_states()

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id
        self._update_button_states()

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        return self._ssh_connection is not None and self._ssh_connection.is_connected()

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        if scan_btn := self._buttons.get("scan"):
            if self._is_connected():
                scan_btn.enable()
            else:
                scan_btn.disable()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._slx_results:
            with self._slx_results:
                ui.label("No SLX operations performed yet").classes("text-gray-500 italic")

    def _add_result_card(self, title: str, content: str, color: str) -> None:
        """Add a result card to the results area."""
        if not self._slx_results:
            return

        with self._slx_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label(title).classes(f"font-bold text-{color}-600")
                ui.label(content).classes("text-sm text-gray-600")

    def _scan_interfaces(self) -> None:
        """Scan SLX interfaces."""
        if not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        self._add_result_card("SLX Interface Scan Completed", "SLX router information would appear here", "red")
        ui.notify("SLX interface scan completed", color="positive")

    def _clear_results(self) -> None:
        """Clear SLX results."""
        if self._slx_results:
            self._slx_results.clear()
            self._show_empty_state()
        ui.notify("Results cleared", color="info")
