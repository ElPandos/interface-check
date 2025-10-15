import logging
import subprocess
from typing import Any

from nicegui import nicegui, ui

from src.core.connect import SshConnection
from src.core.terminal import Cli
from src.models.config import Config
from src.platform.commands import Git
from src.ui.handlers.settings import settings
from src.ui.tabs.agent import AgentPanel, AgentTab
from src.ui.tabs.cable import CablePanel, CableTab
from src.ui.tabs.chat import ChatPanel, ChatTab
from src.ui.tabs.database import DatabasePanel, DatabaseTab
from src.ui.tabs.e2e import E2ePanel, E2eTab
from src.ui.tabs.host import HostPanel, HostTab
from src.ui.tabs.local import LocalPanel, LocalTab
from src.ui.tabs.log import LogPanel, LogTab
from src.ui.tabs.slx import SlxPanel, SlxTab
from src.ui.tabs.system import SystemPanel, SystemTab
from src.ui.tabs.toolbox import ToolboxPanel, ToolboxTab
from src.ui.theme.style import apply_global_theme

logger = logging.getLogger(__name__)


class Gui:
    _config: Config
    _ssh_connection: SshConnection = None
    _tabs: ui.tabs
    _right_drawer: ui.right_drawer
    footer: ui.footer

    _tab_content: dict[str, Any]
    _panel_content: dict[str, Any]

    def __init__(self, config: Config) -> None:
        logger.debug("GUI init")
        logger.debug(f"Nicegui version: {nicegui.__version__}")

        self._config = config
        # self._ssh_connection = SshConnection(self._config)
        self._tab_content = {}
        self._panel_content = {}

        self.build()

    def build(self) -> None:
        apply_global_theme()
        self._add_custom_styles()
        self._build_right_drawer()
        self._build_header()
        self._build_body()
        self._build_footer()
        self._build_sticky_footer()

        self._add_gui_events()

    def run(self) -> None:
        ui.run(favicon="./assets/icons/interoperability.png", reload=True)

    def _build_header(self) -> None:
        with ui.header().classes(replace="row items-center justify-between"):
            with ui.tabs() as self._tabs:
                self._tab_content[LocalTab().name] = LocalTab(build=True)
                self._tab_content[HostTab().name] = HostTab(build=True)
                self._tab_content[ToolboxTab().name] = ToolboxTab(build=True)
                self._tab_content[SlxTab().name] = SlxTab(build=True)
                self._tab_content[CableTab().name] = CableTab(build=True)
                self._tab_content[E2eTab().name] = E2eTab(build=True)
                self._tab_content[SystemTab().name] = SystemTab(build=True)
                self._tab_content[DatabaseTab().name] = DatabaseTab(build=True)
                self._tab_content[LogTab().name] = LogTab(build=True)
                self._tab_content[AgentTab().name] = AgentTab(build=True)
                self._tab_content[ChatTab().name] = ChatTab(build=True)

            # Right drawer button (Toggle will show the right drawer)
            ui.button(on_click=self._right_drawer.toggle, icon="settings").props("flat color=white")

    def _build_body(self) -> None:
        with ui.tab_panels(self._tabs, value=LocalTab().name).classes("w-full h-fit bg-gray-100"):
            dashboard_panel = LocalPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[dashboard_panel.name] = dashboard_panel

            host_panel = HostPanel(
                build=True,
                config=self._config,
                ssh_connection=self._ssh_connection,
                icon=self._tab_content[HostTab().name].icon,
            )
            self._panel_content[host_panel.name] = host_panel

            toolbox_panel = ToolboxPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[toolbox_panel.name] = toolbox_panel

            slx_panel = SlxPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[slx_panel.name] = slx_panel

            cable_panel = CablePanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[cable_panel.name] = cable_panel

            e2e_panel = E2ePanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[e2e_panel.name] = e2e_panel

            system_panel = SystemPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[system_panel.name] = system_panel

            database_panel = DatabasePanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[database_panel.name] = database_panel

            log_panel = LogPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[log_panel.name] = log_panel

            agent_panel = AgentPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[agent_panel.name] = agent_panel

            chat_panel = ChatPanel(build=True, config=self._config, ssh_connection=self._ssh_connection)
            self._panel_content[chat_panel.name] = chat_panel

    def _build_right_drawer(self) -> None:
        with ui.right_drawer().classes("bg-blue-100") as self._right_drawer:
            self._right_drawer.hide()  # Hide as default
            settings.build(self._config)

    def _build_footer(self) -> None:
        with ui.footer(value=False) as self.footer:
            try:
                proc = Cli().run(Git().patchset().syntax)
                stdout, _, returncode = Cli().get_output(proc)
                stdout = stdout.strip() if returncode == 0 else "unknown"
            except (subprocess.SubprocessError, OSError, ValueError):
                stdout = "unknown"
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

    def _on_tab_changes(self, e: Any) -> None:
        pass

    def _add_gui_events(self) -> None:
        self._tabs.on_value_change(self._on_tab_changes)

    def _reload_page(self) -> None:
        ui.navigate.reload()  # Reloads the page without JavaScript

    def _update_tab_panel(self) -> None:
        pass

    def _add_custom_styles(self) -> None:
        """Add custom CSS styles for better tab visibility."""
        ui.add_head_html("""
        <style>
        /* Enhanced tab styling for better visibility */
        .q-tab {
            transition: all 0.3s ease;
            border-radius: 8px 8px 0 0;
            margin: 0 2px;
            background: rgba(255, 255, 255, 0.1);
        }

        .q-tab--active {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #1976d2 !important;
            font-weight: 600;
            box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }

        .q-tab--active .q-icon {
            color: #1976d2 !important;
            transform: scale(1.1);
        }

        .q-tab:not(.q-tab--active):hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
        }

        .q-tabs__content {
            background: rgba(0, 0, 0, 0.05);
            border-radius: 12px;
            padding: 4px;
        }

        /* Fix inconsistent tab sliding direction */
        .q-tab-panels {
            overflow: hidden;
        }

        .q-tab-panel {
            animation: none !important;
            transition: none !important;
        }
        </style>
        """)

    def disconnect(self) -> None:
        self._ssh_connection.disconnect()
