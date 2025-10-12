from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.handlers.host import HostHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.connect import Ssh

NAME = "hosts"
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
        ssh: Ssh | None = None,
        icon: ui.icon | None = None,
    ):
        super().__init__(NAME, LABEL, "home")
        self._app_config = app_config
        self._ssh = ssh
        self._icon = icon
        if build:
            self.build()

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            handler = HostHandler()
            if hasattr(handler, "set_ssh"):
                handler.set_ssh(self._ssh)
            else:
                # Store reference for handler to use if needed
                self._handler = handler

    def _on_connection_success(self) -> None:
        """Handle successful connection."""

    def _on_connection_failure(self) -> None:
        """Handle connection failure."""
