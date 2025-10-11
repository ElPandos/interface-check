import datetime as dt
import logging
from tkinter import XView
from typing import Any
from nicegui import ui

import plotly.graph_objects as go

from src.models.configurations import AppConfig
from src.ui.handlers.graph import GraphHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.collector import PlotSampleData, WorkManager, Worker
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
    _work_manager: WorkManager

    def __init__(self, build: bool = False, app_config: AppConfig = None, ssh_connection: SshConnection = None):
        super().__init__(NAME, LABEL)

        self._app_config = app_config
        self._ssh_connection = ssh_connection
        self._work_manager = WorkManager()

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name):
            with ui.row().classes("w-full items-left"):
                # Build tab info
                super().build()

                # Build selector
                self._build_selector()

    def _close_card(self, card: ui.card, interf: str = None, kill_worker: bool = False) -> None:
        if kill_worker:
            logging.debug("Kill worker")
            self._work_manager.reset()
        card.delete()
        logging.debug("Card deleted")

    def _build_selector(self) -> None:
        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full items-center"):
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
            logging.warning("Failed to install python library: psutil")
            return

        out, err = self._ssh_connection.exec_command(Common().get_interfaces().syntax)
        if err:
            logging.warning("Failed to collect host interface names")
            return

        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
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
            ui.space()
            ui.button("X", on_click=lambda opt=card: self._close_card(opt, True))

    def _activate_workers(self, options: list) -> None:
        for interf in options.value:
            self._work_manager.add(
                Worker(Ethtool().module_info(interf), interf, self._app_config, self._ssh_connection)
            )
            self._build_source(interf)

    def _build_source(self, interf: str) -> None:
        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
            sample = self._work_manager.get_worker(interf).get_first_sample()
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
            ui.space()
            ui.button("X", on_click=lambda opt=card: self._close_card(opt, interf, True))

    def _activate_source(self, interf: str, options: list) -> None:
        for source in options.value:
            self._build_value(interf, source)

    def _build_value(self, interf: str, source: str) -> None:
        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
            samples = self._work_manager.get_worker(interf).get_all_samples()
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
            ui.button("Start", on_click=lambda opt=selection: self._plot_values(interf, source, opt))
            ui.space()
            ui.button("X", on_click=lambda opt=card: self._close_card(opt))

    def _plot_values(self, interf: str, source: str, options: list) -> None:
        gh = GraphHandler()
        for value in options.value:
            gh.add(self._app_config, self._work_manager, interf, source, value)
