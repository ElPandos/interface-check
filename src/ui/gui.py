import logging
from typing import Any
from nicegui import ui, nicegui

from src.models.configurations import AppConfig
from src.ui.handlers.settings import settings
from src.ui.tabs.base import BasePanel, BaseTab
from src.ui.tabs.ethtool import EthtoolPanel, EthtoolTab
from src.ui.tabs.host import HostPanel, HostTab
from src.ui.tabs.info import InfoPanel, InfoTab
from src.ui.tabs.log import LogPanel, LogTab
from src.ui.tabs.mlxconfig import MlxconfigPanel, MlxconfigTab
from src.ui.tabs.mlxlink import MlxlinkPanel, MlxlinkTab
from src.utils.system import get_patchset
from src.utils.ssh_connection import SshConnection


class Gui:
    _app_config: AppConfig
    _ssh_connection: SshConnection

    _tab_content: dict[str, Any] = {}
    _panel_content: dict[str, Any] = {}

    def __init__(self, app_config: AppConfig) -> None:
        logging.debug("GUI init")
        logging.debug(f"Nicegui version: {nicegui.__version__}")

        self._app_config = app_config
        self._ssh_connection = SshConnection(self._app_config)

        self.build()

    def build(self) -> None:
        self._build_right_drawer()
        self._build_header()
        self._build_body()
        self._build_footer()
        self._build_sticky_footer()

        self._add_gui_events()

    def run(self) -> None:
        ui.run(reload=False)

    def _build_header(self) -> None:
        with ui.header().classes(replace="row items-center justify-between"):
            with ui.tabs() as self._tabs:
                self._tab_content[HostTab().name] = HostTab(True)
                self._tab_content[MlxconfigTab().name] = MlxconfigTab(True)
                self._tab_content[MlxlinkTab().name] = MlxlinkTab(True)
                self._tab_content[EthtoolTab().name] = EthtoolTab(True)
                self._tab_content[InfoTab().name] = InfoTab(True)
                self._tab_content[LogTab().name] = LogTab(True)

            # Right drawer button (Toggle will show the right drawer)
            ui.button(on_click=self._right_drawer.toggle, icon="settings").props("flat color=white")

    def _build_body(self) -> None:
        with ui.tab_panels(self._tabs, value=HostTab().name).classes("w-full h-fit bg-gray-100"):
            self._panel_content[HostPanel().name] = HostPanel(
                True, self._app_config, self._ssh_connection, self._tab_content[HostTab().name].icon
            )
            self._panel_content[MlxconfigPanel().name] = MlxconfigPanel(True, self._app_config, self._ssh_connection)
            self._panel_content[MlxlinkPanel().name] = MlxlinkPanel(True, self._app_config, self._ssh_connection)
            self._panel_content[EthtoolPanel().name] = EthtoolPanel(True, self._app_config, self._ssh_connection)
            self._panel_content[InfoPanel().name] = InfoPanel(True, self._app_config, self._ssh_connection)
            self._panel_content[LogPanel().name] = LogPanel(True, self._app_config, self._ssh_connection)

    def _build_right_drawer(self) -> None:
        with ui.right_drawer().classes("bg-blue-100") as self._right_drawer:
            self._right_drawer.hide()  # Hide as default
            settings.build(self._app_config)

    def _build_footer(self) -> None:
        with ui.footer(value=False) as self.footer:
            stdout, _ = get_patchset()
            with ui.row().classes("w-full items-center"):
                # This header is needed to ba able to load icon
                ui.add_head_html(
                    '<link href="https://unpkg.com/eva-icons@1.1.3/style/eva-icons.css" rel="stylesheet" />'
                )
                ui.icon("eva-github").classes("text-4xl items-center")
                ui.label(f" Patchset: {stdout}")

                ui.space()
                ui.button("Reload page", on_click=self._reload_page)
                ui.button("Update tab panel", on_click=self._update_tab_panel)

    def _build_sticky_footer(self) -> None:
        with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
            ui.button(on_click=self.footer.toggle, icon="build_circle").props("fab")

    def _on_tab_changes(self, e):
        pass

    def _add_gui_events(self):
        self._tabs.on_value_change(self._on_tab_changes)

    def _reload_page(self):
        ui.navigate.reload()  # Reloads the page without JavaScript

    def _update_tab_panel(self):
        # ui.tab_panel.update()  # Update the tab panel on client side
        pass

    def disconnect(self) -> None:
        self._ssh_connection.disconnect()
