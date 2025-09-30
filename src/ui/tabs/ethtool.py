from nicegui import ui

from random import random
from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.interface import NetworkInterfaces
import plotly.graph_objects as go

from src.utils.ssh_connection import SshConnection

class EthtoolTab(BaseTab):

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(app_config)

        self._name = "ethtool"
        self._label = "Ethtool"
        self._icon_name = "home_repair_service"

        self._build()

    def _build(self) -> None:
        super()._build()


class EthtoolPanel(BasePanel):

    def __init__(self, app_config: AppConfig, ssh_connection: SshConnection = None):
        super().__init__(app_config, ssh_connection)

        self._name = "ethtool"
        self._label = "Ethtool"

        self._build()

    def _build(self):
        with ui.tab_panel(self._name):
            super()._build()
            with ui.card().classes("w-full items-left"):
                with ui.column().classes("w-full items-left"):
                    ui.select(NetworkInterfaces().list(), multiple=True, value="", label="Interfaces").classes("w-64").props("use-chips")

            with ui.card().classes("w-full items-left"):
                fig = go.Figure()
                fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
                plot = ui.plotly(fig).classes('w-full h-40')

                def add_trace():
                    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[random(), random(), random()]))
                    plot.update()

                ui.button('Add trace', on_click=add_trace)
