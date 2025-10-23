from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "e2e"
LABEL = "E2E"


class E2eTab(BaseTab):
    ICON_NAME: str = "swap_horiz"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class E2ePanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, E2eTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._e2e_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("E2E Testing")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with ui.card().classes(classes):
            # Card header with route selector
            with ui.row().classes("w-full items-center gap-2 p-4 border-b"):
                ui.icon("computer", size="md").classes("text-blue-600")
                ui.label(f"Host {screen_num}").classes("text-lg font-semibold")
                ui.space()

                if screen_num not in self._e2e_screens:
                    self._e2e_screens[screen_num] = E2eContent(
                        None, self._host_handler, self._config, self, screen_num
                    )

                # Route selector in header
                e2e_content = self._e2e_screens[screen_num]
                e2e_content.build_route_selector()

            # Content area
            with ui.column().classes("w-full p-4"):
                e2e_content.build_content(screen_num)


class E2eContent:
    def __init__(
        self,
        ssh_connection: SshConnection | None = None,
        host_handler: Any = None,
        config: Config | None = None,
        parent_panel: E2ePanel | None = None,
        screen_num: int = 1,
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._parent_panel = parent_panel
        self._screen_num = screen_num
        self._selected_route: int | None = None
        self._test_results: ui.column | None = None
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
        """Build E2E testing interface for the screen."""
        # E2E test controls
        with ui.row().classes("w-full gap-2 mt-2"):
            self._buttons["test"] = ui.button(
                "Run E2E Tests", icon="play_arrow", on_click=self._run_e2e_tests
            ).classes("bg-blue-500 hover:bg-blue-600 text-white")

            self._buttons["clear"] = ui.button(
                "Clear Results", icon="clear", on_click=self._clear_results
            ).classes("bg-gray-500 hover:bg-gray-600 text-white")

        # Test results area
        with ui.column().classes("w-full mt-4"):
            ui.label("E2E Test Results").classes("text-lg font-bold")
            self._test_results = ui.column().classes("w-full gap-2")
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
        if test_btn := self._buttons.get("test"):
            if self._is_connected():
                test_btn.enable()
            else:
                test_btn.disable()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._test_results:
            with self._test_results:
                ui.label("No tests executed yet").classes("text-gray-500 italic")

    def _add_result_card(self, title: str, content: str, color: str) -> None:
        """Add a result card to the results area."""
        if not self._test_results:
            return

        with self._test_results, ui.card().classes("w-full p-4 border"):
            ui.label(title).classes(f"font-bold text-{color}-600")
            ui.label(content).classes("text-sm text-gray-600")

    def _run_e2e_tests(self) -> None:
        """Run E2E tests."""
        if not self._is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        self._add_result_card("E2E Tests Executed", "Test results would appear here", "blue")
        ui.notify("E2E tests completed", color="positive")

    def _clear_results(self) -> None:
        """Clear test results."""
        if self._test_results:
            self._test_results.clear()
            self._show_empty_state()
        ui.notify("Results cleared", color="info")

    def update_button_states(self) -> None:
        """Public method to update button states from parent."""
        self._update_button_states()

    def build(self, screen_num: int) -> None:
        """Legacy method for compatibility."""
        self.build_content(screen_num)
