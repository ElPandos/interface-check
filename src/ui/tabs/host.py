from nicegui import ui

from src.ui.handlers.host import HostHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "host"
LABEL = "Host"


class HostTab(BaseTab):
    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, "home")
        if build:
            self.build()


class HostPanel(BasePanel):
    def __init__(self, build=False, app_config=None, ssh_connection: SshConnection = None, icon: ui.icon = None):
        super().__init__(NAME, LABEL)
        self._ssh_connection = ssh_connection
        self._icon = icon
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            handler = HostHandler()
            handler._ssh_connection = self._ssh_connection

    def _on_connection_success(self):
        """Handle successful connection."""
        pass

    def _on_connection_failure(self):
        """Handle connection failure."""
        pass
