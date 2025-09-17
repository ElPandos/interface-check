from enum import Enum


class Options(Enum):
    SWITCH = "Switch"
    SLIDER = "Slider"
    TEXT = "Text"
    INFO = "Info"

    @property
    def name(self) -> str:
        return self.value


class Types(Enum):
    DEBUG = "Debug mode"
    DARK = "Dark mode"
    UPDATE = "Update in seconds"
    MESSAGE = "Message"
    LIBS = "Libs"

    @property
    def name(self) -> str:
        return self.value
