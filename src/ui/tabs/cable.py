from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
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
        cfg: Config = None,
        ssh: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, CableTab.ICON_NAME)
        MultiScreen.__init__(self, CableTab.ICON_NAME)

        self._cfg = cfg
        self._ssh = ssh
        self._host_handler = host_handler
        self._icon = icon
        self._cable_screens: dict[int, Any] = {}

        if host_handler:
            self.set_host_handler(host_handler)

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("Cables")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with ui.card().classes(classes):
            # Card header with route selector
            with ui.row().classes("w-full items-center gap-2 p-4 border-b"):
                ui.icon("computer", size="md").classes("text-blue-600")
                ui.label(f"Host {screen_num}").classes("text-lg font-semibold")
                ui.space()

                if screen_num not in self._cable_screens:
                    self._cable_screens[screen_num] = CableContent(
                        None, self._host_handler, self._cfg, self, screen_num
                    )

                # Route selector in header
                cable_content = self._cable_screens[screen_num]
                cable_content.build_route_selector()

            # Content area
            with ui.column().classes("w-full p-4"):
                cable_content.build_content(screen_num)


class CableContent:
    def __init__(
        self,
        ssh: SshConnection | None = None,
        host_handler: Any = None,
        cfg: Config | None = None,
        parent_panel: CablePanel | None = None,
        screen_num: int = 1,
    ) -> None:
        self._ssh = ssh
        self._host_handler = host_handler
        self._cfg = cfg
        self._parent_panel = parent_panel
        self._screen_num = screen_num
        self._selected_route: int | None = None
        self._scan_results: ui.column | None = None
        self._buttons: dict[str, ui.button] = {}
        self._route_selector: ui.select | None = None

    def build_route_selector(self) -> None:
        """Build route selector in card header."""
        self._route_selector = (
            ui.select(options=[], value=None, label="Connected Routes")
            .classes("w-64")
            .on_value_change(self._on_route_change)
        )
        ui.timer(0.5, self._update_route_options, active=True)

    def build_content(self, screen_num: int) -> None:
        """Build cable interface for the screen."""
        # Cable controls
        with ui.row().classes("w-full gap-2 mt-2"):
            self._buttons["scan"] = ui.button("Scan Interfaces", icon="cable", on_click=self._scan_interfaces).classes(
                "bg-red-500 hover:bg-red-600 text-white"
            )

            self._buttons["clear"] = ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Scan results area
        with ui.column().classes("w-full mt-4"):
            ui.label("Cable Scan Results").classes("text-lg font-bold")
            self._scan_results = ui.column().classes("w-full gap-2")
            self._show_empty_state()

        self._update_button_states()

    def _on_route_change(self, e: Any) -> None:
        """Handle route selection change."""
        if hasattr(e, "value") and e.value is not None:
            self._selected_route = getattr(self, "_route_value_map", {}).get(e.value)
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, self._selected_route)
        else:
            self._selected_route = None
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, None)
        self._update_button_states()

    def _update_route_options(self) -> None:
        """Update route selector options."""
        if not (self._parent_panel and self._route_selector):
            return

        connected_routes = self._parent_panel.get_connected_route_options()
        if not connected_routes:
            self._route_selector.options = []
            self._route_selector.update()
            return

        options = [route["label"] for route in connected_routes]
        values = [route["value"] for route in connected_routes]

        self._route_selector.options = options
        self._route_selector.update()
        self._route_value_map = dict(zip(options, values, strict=False))

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        if self._parent_panel and self._selected_route is not None:
            connection = self._parent_panel.get_screen_connection(self._screen_num)
            return connection is not None and connection.is_connected()
        return False

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        if scan_btn := self._buttons.get("scan"):
            if self._is_connected():
                scan_btn.enable()
            else:
                scan_btn.disable()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._scan_results:
            with self._scan_results:
                ui.label("No interface scans performed yet").classes("text-gray-500 italic")

    def _add_result_card(self, title: str, content: str, color: str) -> None:
        """Add a result card to the results area."""
        if not self._scan_results:
            return

        with self._scan_results, ui.card().classes("w-full p-4 border"):
            ui.label(title).classes(f"font-bold text-{color}-600")
            ui.label(content).classes("text-sm text-gray-600")

    def _scan_interfaces(self) -> None:
        """Scan network interfaces."""
        if not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        self._add_result_card("Interface Scan Completed", "Cable and interface information would appear here", "red")
        ui.notify("Interface scan completed", color="positive")

    def _clear_results(self) -> None:
        """Clear scan results."""
        if self._scan_results:
            self._scan_results.clear()
            self._show_empty_state()
        ui.notify("Results cleared", color="info")

    def update_button_states(self) -> None:
        """Public method to update button states from parent."""
        self._update_button_states()

    def build(self, screen_num: int) -> None:
        """Legacy method for compatibility."""
        self.build_content(screen_num)
