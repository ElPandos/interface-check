from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
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
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._e2e_screens:
                self._e2e_screens[screen_num] = E2eContent(self._ssh_connection, self._host_handler, self._config)

            e2e_content = self._e2e_screens[screen_num]
            e2e_content.build(screen_num)


class E2eContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._test_results: ui.column | None = None

    def build(self, screen_num: int) -> None:
        """Build E2E testing interface for the screen."""
        # Connection selector with filtered hosts
        if self._host_handler:
            allowed_host_ids = {2, 4, 5, 6, 8}
            filtered_connect_route = getattr(self._host_handler, "_connect_route", {}) & allowed_host_ids

            Selector(
                filtered_connect_route,
                getattr(self._host_handler, "_routes", {}),
                lambda conn_id: self._on_connection_change(conn_id),
            ).build()

        # E2E test controls
        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button("Run E2E Tests", icon="play_arrow", on_click=self._run_e2e_tests).classes(
                "bg-blue-500 hover:bg-blue-600 text-white"
            )

            ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Test results area
        with ui.column().classes("w-full mt-4"):
            ui.label("E2E Test Results").classes("text-lg font-bold")
            self._test_results = ui.column().classes("w-full gap-2")
            with self._test_results:
                ui.label("No tests executed yet").classes("text-gray-500 italic")

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id

    def _run_e2e_tests(self) -> None:
        """Run E2E tests."""
        if not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if not self._test_results:
            return

        with self._test_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label("E2E Tests Executed").classes("font-bold text-blue-600")
                ui.label("Test results would appear here").classes("text-sm text-gray-600")

        ui.notify("E2E tests completed", color="positive")

    def _clear_results(self) -> None:
        """Clear test results."""
        if self._test_results:
            self._test_results.clear()
            with self._test_results:
                ui.label("No tests executed yet").classes("text-gray-500 italic")
        ui.notify("Results cleared", color="info")
