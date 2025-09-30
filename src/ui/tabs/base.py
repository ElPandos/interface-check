from nicegui import ui

from src.models.configurations import AppConfig
from src.utils.ssh_connection import SshConnection


class Base:
    _name: str
    _label: str

    _app_config: AppConfig | None
    _ssh_connection: SshConnection | None

    _CONTENT_OF_STRING = "Content of -> "

    def __init__(self, app_config: AppConfig, ssh_connection: SshConnection = None) -> None:
        self._app_config = app_config
        self._ssh_connection = ssh_connection

    def _title(self) -> None:
        ui.label(self._CONTENT_OF_STRING + self._label)

    def _build(self) -> None:
        self._title()

    def get_ssh(self) -> SshConnection:
        return self._ssh_connection


class BaseTab(Base):
    _icon_name: str
    _icon: ui.icon

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(app_config)

    def _build(self) -> None:
        with ui.tab(self._name):
            self._icon = ui.icon(self._icon_name).props('size=24px')

    def get_icon(self) -> ui.icon:
        return self._icon


class BasePanel(Base):

    def __init__(self, app_config: AppConfig, ssh_connection: SshConnection) -> None:
        super().__init__(app_config, ssh_connection)

    def _build(self) -> None:
        super()._build()

    def _save(self) -> None:
        from src.utils.configure import Configure
        Configure().save(self._app_config)

