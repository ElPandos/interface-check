from typing import ClassVar
from pydantic import BaseModel, Field

from src.ui.enums.settings import Options, Types


class Host(BaseModel):
    name: str
    ip: str
    username: str
    password: str
    port: int

    _DEFAULT_HOST: ClassVar[dict] = {
        "name": "default_host_server",
        "ip": "127.0.0.1",
        "username": "user",
        "password": "pass",
        "port": 22,
    }

    _DEFAULT_JUMP: ClassVar[dict] = {
        "name": "default_jump_server",
        "ip": "127.0.0.1",
        "username": "user",
        "password": "pass",
        "port": 22,
    }

    @classmethod
    def default_host(cls) -> "Host":
        """Return a ``Host`` instance pre‑populated with the default host values."""
        return cls._from_defaults(cls._DEFAULT_HOST)

    @classmethod
    def default_jump(cls) -> "Host":
        """Return a ``Host`` instance pre‑populated with the default jump‑host values."""
        return cls._from_defaults(cls._DEFAULT_JUMP)

    @classmethod
    def _from_defaults(cls, defaults: dict) -> "Host":
        """
        Centralised construction helper.

        Parameters
        ----------
        defaults: dict
            Mapping of field names to default values.

        Returns
        -------
        Host
            A new ``Host`` instance.
        """
        # ``SecretStr`` is required for the password field – we wrap it here.
        defaults = defaults.copy()
        # Let Pydantic handle conversion to SecretStr by passing the raw string.
        return cls(**defaults)


class Setting(BaseModel):
    name: str
    type: Options
    value: bool | int | str
    min: int | None = None
    max: int | None = None


class SettingsConfig(BaseModel):
    settings: list[Setting] = Field(
        default_factory=lambda: [
            Setting(
                name=Types.DEBUG.name,
                type=Options.SWITCH,
                value=False,
            ),
            Setting(
                name=Types.DARK.name,
                type=Options.SWITCH,
                value=False,
            ),
            Setting(
                name=Types.UPDATE.name,
                type=Options.SLIDER,
                value=10,
                min=5,
                max=100,
            ),
            Setting(
                name=Types.MESSAGE.name,
                type=Options.TEXT,
                value="Start typing...",
            ),
            Setting(
                name=Types.SAVE.name,
                type=Options.BUTTON,
                value="Save",
            ),
            Setting(
                name=Types.LIBS.name,
                type=Options.INFO,
                value="",
            ),
        ]
    )

    def get_update_value(self) -> int:
        update_setting = next((s for s in self.settings if s.name == Types.UPDATE.name), None)
        if update_setting is None:
            raise ValueError("UPDATE setting not defined in configuration")
        return int(update_setting.value)


class HostsConfig(BaseModel):
    target_host: Host = Field(default_factory=lambda: Host.default_host())
    jump_hosts: list[Host] = Field(default_factory=lambda: [Host.default_jump()])


class AppConfig(BaseModel):
    system: SettingsConfig = Field(default_factory=SettingsConfig)
    hosts: HostsConfig = Field(default_factory=HostsConfig)

    def add_jump(self, host: Host) -> None:
        self.hosts.jump_hosts.append(host)
