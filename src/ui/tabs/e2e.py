from nicegui import ui

from src.mixins.multi_screen import MultiScreenMixin
from src.models.configurations import AppConfig
from src.ui.components.connection_selector import ConnectionSelector
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

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


class E2ePanel(BasePanel, MultiScreenMixin):
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
            self._build_controls_base("E2E Testing")
            self._build_content_base()

    def _build_screen(self, screen_num, classes):
        with ui.card().classes(classes), ui.expansion(f"Host {screen_num}", icon="computer").classes("w-full"):
            if self._host_handler:
                # Filter to only show hosts 2, 4, 5, 6, 8
                allowed_host_ids = {2, 4, 5, 6, 8}
                filtered_connected_routes = self._host_handler._connected_routes & allowed_host_ids  # noqa: SLF001

                ConnectionSelector(
                    filtered_connected_routes,
                    self._host_handler._routes,  # noqa: SLF001
                    lambda conn_id, s=screen_num: self._on_connection_change(conn_id, s),
                ).build()
            ui.button("Run E2E Tests", on_click=lambda s=screen_num: self._run_e2e_tests(s)).classes(
                "bg-blue-300 hover:bg-blue-400 text-blue-900 mt-2"
            )
            ui.label(f"E2E testing for host {screen_num}").classes("mt-4")

    def _run_e2e_tests(self, screen_num):
        ui.notify(f"Running E2E tests for screen {screen_num}", color="info")
