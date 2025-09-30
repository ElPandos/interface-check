from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.handlers.settings import settings
from src.ui.tabs.host import HostTab, HostPanel
from src.ui.tabs.mlxlink import MlxlinkTab, MlxlinkPanel
from src.ui.tabs.mlxconfig import MlxconfigTab, MlxconfigPanel
from src.ui.tabs.ethtool import EthtoolTab, EthtoolPanel
from src.ui.tabs.info import InfoTab, InfoPanel
from src.ui.tabs.log import LogTab, LogPanel

from src.utils import ethtool
from src.utils.process_manager import ProcessManager
from src.utils.ssh_connection import SshConnection


class Gui:

    _app_config: AppConfig
    _ssh_connection: SshConnection

    def __init__(self, app_config: AppConfig) -> None:
        ui.query(".nicegui-content").classes("p-0 w-full")
        ui.query(".q-page").classes("flex")

        self._app_config = app_config
        self._ssh_connection = SshConnection(self._app_config)

        self._header()
        self._body()
        self._right_drawer()
        self._footer()
        self._sticky_footer()

        ui.run()

    def _header(self) -> None:
        with ui.header().classes(replace="row items-center justify-between"):
            with ui.tabs() as self._tabs:
                self.host_tab = HostTab(self._app_config)
                self.mlxconfig_tab = MlxconfigTab(self._app_config)
                self.mlxlink_tab = MlxlinkTab(self._app_config)
                self.ethtool_tab = EthtoolTab(self._app_config)
                self.info_tab = InfoTab(self._app_config)
                self.log_tab = LogTab(self._app_config)

            # Drawer button
            ui.button(on_click=lambda: self.right_drawer.toggle(), icon="settings").props("flat color=white")

    def _body(self) -> None:
        with ui.tab_panels(self._tabs, value="host").classes("w-full h-fit bg-gray-100"):
            self.host_panel = HostPanel(self._app_config, self.host_tab.get_icon(), self._ssh_connection)

            self.mlxconfig_panel = MlxconfigPanel(self._app_config, self._ssh_connection)
            self.mlxlink_panel = MlxlinkPanel(self._app_config, self._ssh_connection)
            self.ethtool_panel = EthtoolPanel(self._app_config, self._ssh_connection)
            self.info_panel = InfoPanel(self._app_config, self._ssh_connection)
            self.log_panel = LogPanel(self._app_config, self._ssh_connection)

    def _right_drawer(self) -> None:
        with ui.right_drawer().classes("bg-blue-100") as self.right_drawer:
            self.right_drawer.hide()  # Hide as default
            settings.build(self._app_config)

    def _footer(self) -> None:
        with ui.footer(value=False) as self.footer:
            pm = ProcessManager()
            proc = pm.run('git describe --all --long | cut -d "-" -f 3')
            stdout, stderr = pm.get_output(proc)
            #logger.debug(f"Footer: STDOUT: {stdout}")
            #logger.debug(f"Footer: STDERR: {stderr}")

            with ui.row().classes("w-full items-center"):
                ui.add_head_html(
                    '<link href="https://unpkg.com/eva-icons@1.1.3/style/eva-icons.css" rel="stylesheet" />'
                )
                ui.icon("eva-github").classes("text-4xl items-center")
                ui.label(f" Patchset: {stdout}")

    def _sticky_footer(self) -> None:
        with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
            ui.button(on_click=self.footer.toggle, icon="build_circle").props("fab")
