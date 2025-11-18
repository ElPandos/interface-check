from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr

from src.ui.enums.settings import Options, Types


class Host(BaseModel):
    """Host configuration - role determined by route context."""

    ip: str = ""
    username: str = ""
    password: SecretStr = SecretStr("")
    info: str = ""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_encoders={SecretStr: lambda v: v.get_secret_value()}
    )

    @classmethod
    def default_jump(cls) -> "Host":
        """Return default jump host configuration.

        Returns:
            Default jump host
        """
        return cls(
            ip="137.58.231.134", username="emvekta", password=SecretStr("a"), info="Default value"
        )

    @classmethod
    def default_target(cls) -> "Host":
        """Return default target host configuration.

        Returns:
            Default target host
        """
        return cls(ip="172.16.180.1", username="hts", password=SecretStr("a"), info="Default value")


class Jump(Host):
    """Single jump in SSH tunnel chain."""

    host: Host
    order: int = 1


class Route(BaseModel):
    """Connection path through multiple hosts."""

    summary: str
    target: Host
    jumps: list[Host] = Field(default_factory=list)

    @classmethod
    def default_route(cls) -> "Route":
        """Return default route configuration.

        Returns:
            Default route
        """
        return cls(
            summary="137.58.231.134 ⟶ 172.16.180.1 (Target)",
            target=Host.default_target(),
            jumps=[Host.default_jump()],
        )


class Option(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(use_enum_values=True)

    name: str = ""
    type: Options = Options.SWITCH
    value: bool | int | str = False
    min: int | None = None
    max: int | None = None

    @classmethod
    def default_debug(cls) -> "Option":
        """Return default debug configuration.

        Returns:
            Default debug option
        """
        return cls(
            name=Types.DEBUG.value,
            type=Options.SWITCH,
            value=False,
        )

    @classmethod
    def default_dark(cls) -> "Option":
        """Return default dark configuration.

        Returns:
            Default dark option
        """
        return cls(
            name=Types.DARK.value,
            type=Options.SWITCH,
            value=False,
        )

    @classmethod
    def default_command(cls) -> "Option":
        """Return default command configuration.

        Returns:
            Default command option
        """
        return cls(
            name=Types.COMMAND.value,
            type=Options.SLIDER,
            value=10,
            min=3,
            max=100,
        )

    @classmethod
    def default_graph(cls) -> "Option":
        """Return default graph configuration.

        Returns:
            Default graph option
        """
        return cls(
            name=Types.GRAPH.value,
            type=Options.SLIDER,
            value=10,
            min=10,
            max=100,
        )

    @classmethod
    def default_refresh(cls) -> "Option":
        """Return default refresh configuration.

        Returns:
            Default refresh option
        """
        return cls(
            name=Types.REFRESH.value,
            type=Options.SLIDER,
            value=5,
            min=1,
            max=60,
        )

    @classmethod
    def default_message(cls) -> "Option":
        """Return default message configuration.

        Returns:
            Default message option
        """
        return cls(
            name=Types.MESSAGE.value,
            type=Options.TEXT,
            value="Start typing...",
        )

    @classmethod
    def default_save(cls) -> "Option":
        """Return default save configuration.

        Returns:
            Default save option
        """
        return cls(
            name=Types.SAVE.value,
            type=Options.BUTTON,
            value="Save",
        )

    @classmethod
    def default_libs(cls) -> "Option":
        """Return default libs configuration.

        Returns:
            Default libs option
        """
        return cls(
            name=Types.LIBS.value,
            type=Options.INFO,
            value="",
        )


class Settings(BaseModel):
    options: list[Option] = Field(
        default_factory=lambda: [
            Option.default_debug(),
            Option.default_dark(),
            Option.default_command(),
            Option.default_graph(),
            Option.default_refresh(),
            Option.default_message(),
            Option.default_save(),
            Option.default_libs(),
        ]
    )

    def get_command_update_value(self) -> int:
        """Get command update value.

        Returns:
            Command update interval
        """
        command_update = next((s for s in self.settings if s.name == Types.COMMAND.value), None)
        if command_update is None:
            msg = "UPDATE setting not defined in configuration"
            raise ValueError(msg)
        return int(command_update.value)

    def get_graph_update_value(self) -> int:
        """Get graph update value.

        Returns:
            Graph update interval
        """
        graph_update = next((s for s in self.settings if s.name == Types.GRAPH.value), None)
        if graph_update is None:
            msg = "UPDATE setting not defined in configuration"
            raise ValueError(msg)
        return int(graph_update.value)


class Networks(BaseModel):
    """Networks configuration with hosts and connection paths."""

    hosts: list[Host] = Field(default_factory=lambda: [Host.default_jump(), Host.default_target()])
    routes: list[Route] = Field(default_factory=lambda: [Route.default_route()])


class Config(BaseModel):
    """Application configuration."""

    settings: Settings = Field(default_factory=Settings)
    networks: Networks = Field(default_factory=Networks)
