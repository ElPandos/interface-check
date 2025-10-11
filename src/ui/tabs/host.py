from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.handlers.host import HostHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "host"
LABEL = "Host"


class HostTab(BaseTab):
    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, "home")
        if build:
            self.build()


class HostPanel(BasePanel):
    def __init__(
        self,
        *,
        build: bool = False,
        app_config: AppConfig,
        ssh_connection: SshConnection | None = None,
        icon: ui.icon | None = None,
    ):
        super().__init__(NAME, LABEL)
        self._app_config = app_config
        self._ssh_connection = ssh_connection
        self._icon = icon
        if build:
            self.build()

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            handler = HostHandler()
            if hasattr(handler, "set_ssh_connection"):
                handler.set_ssh_connection(self._ssh_connection)
            else:
                # Store reference for handler to use if needed
                self._handler = handler

    def _on_connection_success(self) -> None:
        """Handle successful connection."""

    def _on_connection_failure(self) -> None:
        """Handle connection failure."""
