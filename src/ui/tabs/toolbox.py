from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
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
            if self._host_handler:
                self.set_host_handler(self._host_handler)
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with ui.card().classes(classes):
            # Card header with route selector
            with ui.row().classes("w-full items-center gap-2 p-4 border-b"):
                ui.icon("computer", size="md").classes("text-blue-600")
                ui.label(f"Host {screen_num}").classes("text-lg font-semibold")
                ui.space()

                if screen_num not in self._toolbox_screens:
                    self._toolbox_screens[screen_num] = ToolboxContent(
                        self._ssh_connection, self._host_handler, self._config, self, screen_num
                    )

                # Route selector in header
                toolbox_content = self._toolbox_screens[screen_num]
                toolbox_content.build_route_selector()

            # Content area
            with ui.column().classes("w-full p-4"):
                toolbox_content.build_content(screen_num)


class ToolboxContent:
    def __init__(
        self,
        ssh_connection: SshConnection | None = None,
        host_handler: Any = None,
        config: Config | None = None,
        parent_panel: ToolboxPanel | None = None,
        screen_num: int = 1,
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._parent_panel = parent_panel
        self._screen_num = screen_num
        self._selected_route: int | None = None
        self._tool_results: ui.column | None = None
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

    def build_content(self) -> None:
        """Build toolbox content area."""
        # Controls
        with ui.row().classes("w-full gap-2 mb-4 flex-wrap"):
            self._buttons["scan"] = ui.button(
                "Scan Interfaces", icon="search", on_click=self._scan_interfaces
            ).classes("bg-red-500 hover:bg-red-600 text-white")
            self._buttons["tools"] = ui.button(
                "Network Tools", icon="build", on_click=self._network_tools
            ).classes("bg-blue-500 hover:bg-blue-600 text-white")
            self._buttons["clear"] = ui.button(
                "Clear Results", icon="clear", on_click=self._clear_results
            ).classes("bg-gray-500 hover:bg-gray-600 text-white")

        # Results area
        with ui.column().classes("w-full"):
            ui.label("Toolbox Results").classes("text-lg font-bold mb-2")
            self._tool_results = ui.column().classes("w-full gap-2")
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
        is_connected = self._is_connected()
        for button_name in ("scan", "tools"):
            if button := self._buttons.get(button_name):
                if is_connected:
                    button.enable()
                else:
                    button.disable()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._tool_results:
            with self._tool_results:
                ui.label("No tools executed yet").classes("text-gray-500 italic")

    def _add_result_card(self, title: str, content: str, color: str) -> None:
        """Add a result card to the results area."""
        if not self._tool_results:
            return

        with self._tool_results, ui.card().classes("w-full p-4 border"):
            ui.label(title).classes(f"font-bold text-{color}-600")
            ui.label(content).classes("text-sm text-gray-600")

    def _scan_interfaces(self) -> None:
        """Scan network interfaces."""
        if not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        self._add_result_card(
            "Interface Scan Completed", "Network interface information would appear here", "red"
        )
        ui.notify("Interface scan completed", color="positive")

    def _network_tools(self) -> None:
        """Run network tools."""
        if not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        self._add_result_card(
            "Network Tools Executed", "Network diagnostic tools results would appear here", "blue"
        )
        ui.notify("Network tools completed", color="positive")

    def _clear_results(self) -> None:
        """Clear tool results."""
        if self._tool_results:
            self._tool_results.clear()
            self._show_empty_state()
        ui.notify("Results cleared", color="info")

    def update_button_states(self) -> None:
        """Public method to update button states from parent."""
        self._update_button_states()

    def build(self, screen_num: int) -> None:
        """Legacy method for compatibility."""
        self.build_content(screen_num)
