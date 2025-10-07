import logging
from nicegui import ui

import plotly.graph_objects as go

from src.models.configurations import AppConfig, Host
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection


NAME = "host"
LABEL = "Host"


class HostTab(BaseTab):
    ICON_NAME: str = "home"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class HostPanel(BasePanel):
    _app_config: AppConfig
    _icon: ui.icon

    def __init__(
        self, build=False, app_config: AppConfig = None, ssh_connection: SshConnection = None, icon: ui.icon = None
    ):
        super().__init__(NAME, LABEL)

        self._app_config = app_config
        self.ssh_connection = ssh_connection
        self._icon = icon

        if build:
            self.build()

    # @ui.refreshable
    def build(self):
        with ui.tab_panel(self.name):
            with ui.column():
                # Build tab info
                super().build()

                # Build panel
                self._build_remote_target()
                self._build_jump_hosts()
                self._build_buttons()

    # def refresh(self):
    #     self.build.refresh()

    def _build_remote_target(self) -> None:
        with ui.card().classes("w-full"):
            # Title
            ui.label("Remote host").classes("text-lg font-medium")

            # Name
            ui.input(label="Name").props("outlined dense").bind_value(self._app_config.hosts.target_host, "name")

            # IP address
            ui.input(label="IP").props("outlined dense").bind_value(self._app_config.hosts.target_host, "ip")

            # Username
            ui.input(label="Username").props("outlined dense").bind_value(
                self._app_config.hosts.target_host, "username"
            )

            # Password (masked)
            ui.input(label="Password", password=True).props("outlined dense").bind_value(
                self._app_config.hosts.target_host, "password"
            )

    def _build_jump_hosts(self) -> None:
        with ui.card().classes("w-full"):
            for idx, jump in enumerate(self._app_config.hosts.jump_hosts):
                # Each `jump` is a plain object (e.g. a dataclass) that has name/ip/username/password attributes
                with ui.expansion(f"Jump host {idx + 1}").classes("w-full"):
                    # Name
                    ui.input(placeholder="Name", label="Name").props("outlined dense").bind_value(jump, "name")

                    # IP address
                    ui.input(placeholder="IP", label="IP").props("outlined dense").bind_value(jump, "ip")

                    # Username
                    ui.input(placeholder="Username", label="Username").props("outlined dense").bind_value(
                        jump, "username"
                    )

                    # Password (masked)
                    ui.input(placeholder="Password", label="Password", password=True).props(
                        "outlined dense"
                    ).bind_value(jump, "password")

    def _build_buttons(self) -> None:
        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center"):
                self._connect_button = ui.button("Connect", on_click=self._connect)
                ui.button("Add jump host", on_click=self._add_jump_host).props("color-primary")
                ui.space()
                ui.button("Save", on_click=self.save).props("color-primary")

    def _connect(self) -> None:
        """Update tab icon colour depending on connection state."""
        try:
            if not self.is_connected():
                self.ssh_connection.connect()
                self._icon.style("color: limegreen;")  # font-size: 24px;")
                self._connect_button.set_text("Disconnect")
            else:
                self.ssh_connection.disconnect()
                self._icon.style("color: white;")  # font-size: 24px;")
                self._connect_button.set_text("Connect")
        except RuntimeError as e:
            logging.error(f"SSH connection failed: {e}")

    def _add_jump_host(self) -> None:
        logging.warning("Not yet implemented...")
        # No jump host addition logic implemented yet.
        # self._app_config.add_jump(Host().default_jump())
        pass

    def is_connected(self) -> bool:
        if not self.ssh_connection:
            return False
        return self.ssh_connection.is_connected()
