import logging
from time import time
from typing import Any
from nicegui import ui

import plotly.graph_objects as go

from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.collector import WorkManager, Worker
from src.utils.commands import Common, Modify, System, Ethtool
from src.utils.ssh_connection import SshConnection


NAME = "ethtool"
LABEL = "Ethtool"


class EthtoolTab(BaseTab):
    ICON_NAME: str = "home_repair_service"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class EthtoolPanel(BasePanel):
    _worker_manager: WorkManager

    def __init__(self, build: bool = False, app_config: AppConfig = None, ssh_connection: SshConnection = None):
        super().__init__(NAME, LABEL)

        self._app_config = app_config
        self._ssh_connection = ssh_connection
        self._worker_manager = WorkManager()

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name):
            with ui.row().classes("w-full items-left"):
                # Build tab info
                super().build()

                # Build selector
                self._build_selector()

    # def refresh(self):
    #    self.build.refresh()

    # @ui.refreshable
    def _build_selector(self) -> None:
        with ui.row().classes("w-full items-center"):
            with ui.card().classes("w-full"):
                ui.button("Scan interfaces", on_click=self._scan_interfaces)

    def _scan_interfaces(self):
        if not self._ssh_connection:
            logging.warning("No SSH connection object")
            return

        if not self._ssh_connection.is_connected():
            logging.warning("No SSH connection established")
            return

        _, err = self._ssh_connection.exec_command(System().install_psutil().syntax)
        if err:
            ui.notify("Failed to install python library: psutil", color="warning")
            return

        out, err = self._ssh_connection.exec_command(Common().get_interfaces().syntax)
        if err:
            ui.notify("Failed to collect host interface names", color="warning")
            return

        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                selection = (
                    ui.select(
                        Modify().to_list(out),
                        multiple=True,
                        value=None,
                        label="Interfaces",
                    )
                    .classes("w-40")
                    .classes("w-64")
                    .props("use-chips")
                )

                ui.button("Start", on_click=lambda opt=selection: self._activate_workers(opt))

    def _activate_workers(self, options: list) -> None:
        for interf in options.value:
            self._worker_manager.add(
                Worker(Ethtool().module_info(interf), interf, self._app_config, self._ssh_connection)
            )
            self._build_source(interf)

    def _build_source(self, interf: str) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                sample = self._worker_manager.get_worker(interf).get_first_sample()
                selection = (
                    ui.select(
                        list(sample.snapshot.keys()),
                        multiple=True,
                        value=None,
                        label="Source",
                    )
                    .classes("w-40")
                    .classes("w-64")
                    .props("use-chips")
                )
                ui.button("Start", on_click=lambda opt=selection: self._activate_source(interf, opt))

    def _activate_source(self, interf: str, options: list) -> None:
        for source in options.value:
            self._build_value(interf, source)

    def _build_value(self, interf: str, source: str) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                samples = self._worker_manager.get_worker(interf).get_all_samples()
                selection = (
                    ui.select(
                        list(samples[0].snapshot[source].keys()),
                        multiple=True,
                        value=None,
                        label="value",
                    )
                    .classes("w-40")
                    .classes("w-64")
                    .props("use-chips")
                )
                ui.button("Start", on_click=lambda opt=selection: self._activate_value(interf, source, opt))

    def _activate_value(self, interf: str, source: str, options: list) -> None:
        for value in options.value:
            self._build_plot(interf, source, value)

    def _build_plot(self, interf: str, source: str, value: str) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full"):
                fig = go.Figure()
                plot = ui.plotly(fig).classes("w-full h-80")
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))

                def add_line() -> None:
                    # Clear all existing traces
                    fig.data = []

                    samples = self._worker_manager.get_worker(interf).get_all_samples()

                    y_value = []
                    x_value = []
                    y_axis_label = ""
                    for i in samples:
                        v = i.snapshot[source]
                        v1 = v[value]
                        if type(v1) is list and len(v1) == 2:
                            v1 = v1[0]
                        v2 = v1.value
                        y_axis_label = v1.unit
                        x_value.append(i.begin)
                        y_value.append(v2)

                    fig.update_layout(
                        margin=dict(l=10, r=10, t=30, b=10),
                        title=f"Interface: {interf}, Source: {source}, Value: {value}",
                        #xaxis_title=f"Time",
                        yaxis_title=f"{y_axis_label}",
                        legend_title="Legend",
                        xaxis=dict(type="date", tickformat="%d %b %H:%M:%S", tickangle=-45),
                    )
                    fig.add_trace(go.Scatter(x=x_value, y=y_value))
                    plot.update()

                ui.button("Render graph", on_click=add_line)
