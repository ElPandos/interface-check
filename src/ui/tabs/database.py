"""Database tab implementation."""

from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.mixins.multi_screen import MultiScreenMixin
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

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


class DatabasePanel(BasePanel, MultiScreenMixin):
    def __init__(
        self,
        build: bool = False,
        app_config: AppConfig = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL)
        MultiScreenMixin.__init__(self)
        self._app_config = app_config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_controls_base("Database")
            self._build_content_base()

    def _build_screen(self, screen_num, classes):
        with ui.card().classes(classes):
            with ui.expansion(f"Host {screen_num}", icon="computer").classes("w-full"):
                if self._host_handler:
                    from src.ui.components.connection_selector import ConnectionSelector

                    ConnectionSelector(
                        self._host_handler._connected_routes,
                        self._host_handler._routes,
                        lambda conn_id, s=screen_num: self._on_connection_change(conn_id, s),
                    ).build()
                ui.button("Query Database", on_click=lambda s=screen_num: self._query_database(s)).classes(
                    "bg-blue-300 hover:bg-blue-400 text-blue-900 mt-2"
                )
                ui.label(f"Database content for host {screen_num}").classes("mt-4")

    def _query_database(self, screen_num):
        ui.notify(f"Querying database for screen {screen_num}", color="info")
