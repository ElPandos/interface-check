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
        self._buttons: dict[str, ui.button] = {}

    def build(self, screen_num: int) -> None:
        """Build E2E testing interface for the screen."""
        # Connection selector with filtered hosts
        if self._host_handler:
            # TODO: Implement proper connection selector with SelectionProvider
            ui.label("Connection selector placeholder (filtered hosts)").classes("text-gray-500")

        # E2E test controls
        with ui.row().classes("w-full gap-2 mt-2"):
            self._buttons["test"] = ui.button("Run E2E Tests", icon="play_arrow", on_click=self._run_e2e_tests).classes(
                "bg-blue-500 hover:bg-blue-600 text-white"
            )

            self._buttons["clear"] = ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Test results area
        with ui.column().classes("w-full mt-4"):
            ui.label("E2E Test Results").classes("text-lg font-bold")
            self._test_results = ui.column().classes("w-full gap-2")
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

        with self._test_results:
            with ui.card().classes("w-full p-4 border"):
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
