from pydantic import BaseModel, Field

from src.ui.enums.settings import Options, Types


class Host(BaseModel):
    name: str
    ip: str
    username: str
    password: str
    port: int


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


class HostsConfig(BaseModel):
    target_host: Host = Field(
        default_factory=lambda: Host(
            name="dev_server",
            ip="127.0.0.1",
            username="user",
            password="pass",  # noqa: S106
            port=22,
        )
    )

    jump_hosts: list[Host] = Field(
        default_factory=lambda: [
            Host(
                name="jump_1",
                ip="10.0.0.1",
                username="user1",
                password="pass1",  # noqa: S106
                port=22,
            )
        ]
    )


class AppConfig(BaseModel):
    system: SettingsConfig = Field(default_factory=SettingsConfig)
    hosts: HostsConfig = Field(default_factory=HostsConfig)
