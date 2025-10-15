"""Database tab implementation."""

from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "database"
LABEL = "Database"


class DatabaseTab(BaseTab):
    ICON_NAME: str = "storage"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class DatabasePanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, DatabaseTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._database_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("Database")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._database_screens:
                self._database_screens[screen_num] = DatabaseContent(
                    self._ssh_connection, self._host_handler, self._config
                )

            database_content = self._database_screens[screen_num]
            database_content.build(screen_num)


class DatabaseContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._query_results: ui.column | None = None

    def build(self, screen_num: int) -> None:
        """Build database interface for the screen."""
        # Connection selector
        if self._host_handler:
            Selector(
                getattr(self._host_handler, "_connect_route", {}),
                getattr(self._host_handler, "_routes", {}),
                lambda conn_id: self._on_connection_change(conn_id),
            ).build()

        # Database controls
        with ui.row().classes("w-full gap-2 mt-2"):
            ui.button("Query Database", icon="search", on_click=self._query_database).classes(
                "bg-blue-500 hover:bg-blue-600 text-white"
            )

            ui.button("Clear Results", icon="clear", on_click=self._clear_results).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # Results area
        with ui.column().classes("w-full mt-4"):
            ui.label("Database Results").classes("text-lg font-bold")
            self._query_results = ui.column().classes("w-full gap-2")
            with self._query_results:
                ui.label("No queries executed yet").classes("text-gray-500 italic")

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id

    def _query_database(self) -> None:
        """Execute database query."""
        if not self._ssh_connection or not self._ssh_connection.is_connected():
            ui.notify("SSH connection required", color="negative")
            return

        if not self._query_results:
            return

        # Simulate database query
        with self._query_results:
            with ui.card().classes("w-full p-4 border"):
                ui.label("Query executed successfully").classes("font-bold text-green-600")
                ui.label("Sample database content would appear here").classes("text-sm text-gray-600")

        ui.notify("Database query executed", color="positive")

    def _clear_results(self) -> None:
        """Clear query results."""
        if self._query_results:
            self._query_results.clear()
            with self._query_results:
                ui.label("No queries executed yet").classes("text-gray-500 italic")
        ui.notify("Results cleared", color="info")
