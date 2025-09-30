from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

class MlxconfigTab(BaseTab):

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(app_config)

        self._name = "mlxconfig"
        self._label = "Mlxconfig"
        self._icon_name = "home_repair_service"

        self._build()

    def _build(self) -> None:
        super()._build()


class MlxconfigPanel(BasePanel):

    def __init__(self, app_config: AppConfig, ssh_connection: SshConnection = None):
        super().__init__(app_config, SshConnection)

        self._name = "mlxconfig"
        self._label = "Mlxconfig"

        self._build()

    def _build(self):
        with ui.tab_panel(self._name):
            super()._build()
            with ui.card().classes("w-full"):
                super()._build()
