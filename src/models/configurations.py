from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from src.ui.enums.settings import Options, Types


class Host(BaseModel):
    ip: str
    username: str
    password: SecretStr
    remote: bool = False
    jump: bool = False
    jump_order: int | None = None

    _DEFAULT_HOST: ClassVar[dict[str, str | bool | int | None]] = {
        "ip": "192.168.1.10",
        "username": "admin",
        "password": "demo123",
        "remote": False,
        "jump": False,
        "jump_order": None,
    }

    _DEFAULT_JUMP: ClassVar[dict[str, str | bool | int | None]] = {
        "ip": "10.0.0.5",
        "username": "user",
        "password": "demo456",
        "remote": False,
        "jump": True,
        "jump_order": 1,
    }

    @classmethod
    def default_host(cls) -> "Host":
        """Return a ``Host`` instance pre-populated with the default host values."""
        return cls._from_defaults(cls._DEFAULT_HOST)

    @classmethod
    def default_jump(cls) -> "Host":
        """Return a ``Host`` instance pre-populated with the default jump-host values."""
        return cls._from_defaults(cls._DEFAULT_JUMP)

    @classmethod
    def _from_defaults(cls, defaults: dict[str, str | bool | int | None]) -> "Host":
        """
        Centralised construction helper.

        Parameters
        ----------
        defaults: dict
            Mapping of field names to default values.

        Returns:
        -------
        Host
            A new ``Host`` instance.
        """
        # ``SecretStr`` is required for the password field - we wrap it here.
        defaults = defaults.copy()
        # Let Pydantic handle conversion to SecretStr by passing the raw string.
        return cls(**defaults)


class Setting(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

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
                name=Types.COMMAND.name,
                type=Options.SLIDER,
                value=10,
                min=3,
                max=100,
            ),
            Setting(
                name=Types.GRAPH.name,
                type=Options.SLIDER,
                value=10,
                min=10,
                max=100,
            ),
            # AUTO setting removed - each tab has its own checkbox
            Setting(
                name=Types.REFRESH.name,
                type=Options.SLIDER,
                value=5,
                min=1,
                max=60,
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

    def get_command_update_value(self) -> int:
        command_update = next((s for s in self.settings if s.name == Types.COMMAND.name), None)
        if command_update is None:
            msg = "UPDATE setting not defined in configuration"
            raise ValueError(msg)
        return int(command_update.value)

    def get_graph_update_value(self) -> int:
        graph_update = next((s for s in self.settings if s.name == Types.GRAPH.name), None)
        if graph_update is None:
            msg = "UPDATE setting not defined in configuration"
            raise ValueError(msg)
        return int(graph_update.value)


class AppConfig(BaseModel):
    system: SettingsConfig = Field(default_factory=SettingsConfig)
    hosts: list[Host] = Field(default_factory=lambda: [Host.default_host(), Host.default_jump()])
    routes: list[dict[str, str | list[dict[str, str | int]]]] = Field(default_factory=list)
