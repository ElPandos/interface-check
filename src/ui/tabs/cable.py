from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.mixins.multi_screen import MultiScreenMixin
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "cable"
LABEL = "Cable End to End"


class CableTab(BaseTab):
    ICON_NAME: str = "cable"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class CablePanel(BasePanel, MultiScreenMixin):
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
            self._build_controls_base("Cable End to End")
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
                ui.button("Scan Interfaces", on_click=lambda s=screen_num: self._scan_interfaces(s)).classes(
                    "bg-red-300 hover:bg-red-400 text-red-900 mt-2"
                )
                ui.label(f"Content for host {screen_num}").classes("mt-4")

    def _scan_interfaces(self, screen_num):
        ui.notify(f"Scanning interfaces for screen {screen_num}", color="info")
