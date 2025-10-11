import logging
from nicegui import ui

import plotly.graph_objects as go

from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection


NAME = "mlxconfig"
LABEL = "Mlxconfig"


class MlxconfigTab(BaseTab):
    ICON_NAME = "home_repair_service"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class MlxconfigPanel(BasePanel):
    def __init__(self, build: bool = False, app_config: AppConfig = None, ssh_connection: SshConnection = None):
        super().__init__(NAME, LABEL)

        self._app_config = app_config
        self._ssh_connection = ssh_connection

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name):
            # Build tab info
            super().build()

            # Build selector
            self._build_selector()

    def _build_selector(self) -> None:
        with ui.card().classes("w-full"):
            pass
