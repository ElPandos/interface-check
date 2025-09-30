from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.tabs.base import BaseTab, BasePanel
from src.utils.ssh_connection import SshConnection

class HostTab(BaseTab):

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(app_config)

        self._name = "host"
        self._label = "Host"
        self._icon_name = "home"

        self._build()

    def _build(self) -> None:
        super()._build()


class HostPanel(BasePanel):
    _icon: ui.icon

    def __init__(self, app_config: AppConfig, icon: ui.icon = None, ssh_connection: SshConnection = None):
        super().__init__(app_config, ssh_connection)

        self._name = "host"
        self._label = "Host"

        self._build(icon)

    def _build(self, icon: ui.icon = None):
        self._icon = icon

        with ui.tab_panel(self._name):
            super()._build()
            with ui.card().classes("w-full"):

                # Title
                ui.label("Remote host").classes("text-lg font-medium")

                # Name
                ui.input(
                    label="Name"
                ).props("outlined dense").bind_value(self._app_config.hosts.target_host, "name")

                # IP address
                ui.input(
                    label="IP"
                ).props("outlined dense").bind_value(self._app_config.hosts.target_host, "ip")

                # Username
                ui.input(
                    label="Username"
                ).props("outlined dense").bind_value(self._app_config.hosts.target_host, "username")

                # Password (masked)
                ui.input(
                    label="Password",
                    password=True
                ).props("outlined dense").bind_value(self._app_config.hosts.target_host, "password")

            with ui.card().classes("w-full"):
                for idx, jump in enumerate(self._app_config.hosts.jump_hosts):
                    # each `jump` is a plain object (e.g. a dataclass) that has name/ip/username/password attributes
                    with ui.expansion(f"Jump host {idx + 1}").classes("w-full"):

                        # Name
                        ui.input(
                            placeholder="Name",
                            label="Name"
                        ).props("outlined dense").bind_value(jump, "name")

                        # IP address
                        ui.input(
                            placeholder="IP",
                            label="IP"
                        ).props("outlined dense").bind_value(jump, "ip")

                        # Username
                        ui.input(
                            placeholder="Username",
                            label="Username"
                        ).props("outlined dense").bind_value(jump, "username")

                        # Password (masked)
                        ui.input(
                            placeholder="Password",
                            label="Password",
                            password=True
                        ).props("outlined dense").bind_value(jump, "password")

            with ui.row().classes("w-full items-center"):
                self._connect_button = ui.button("Connect", on_click=self._connect)

                ui.button("Add jump host", on_click=self._add_jump_host).props("color-primary")
                ui.space()
                ui.button("Save", on_click=self._save).props("color-primary")

    def _connect(self) -> None:
        """Update tab icon colour and size depending on state."""
        try:
            if not self.is_connected():
                self._icon.style('color: limegreen; font-size: 24px;')
                self._connect_button.set_text("Disconnect")
                self.get_ssh().connect()
            else:
                self._icon.style('color: white; font-size: 24px;')
                self._connect_button.set_text("Connect")
                self.get_ssh().disconnect()
        except RuntimeError as e:
            print(f"Connection failed failed: {e}")

    def _add_jump_host(self) -> None:
        print("Not yet implemented...")
        pass

    def is_connected(self) -> bool:
        if not self.get_ssh():
            return False
        return self.get_ssh().is_connected()




