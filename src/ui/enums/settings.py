from enum import Enum


class Options(Enum):
    SWITCH = "Switch"
    SLIDER = "Slider"
    TEXT = "Text"
    BUTTON = "Button"
    INFO = "Info"

    @property
    def name(self) -> str:
        return self.value


class Types(Enum):
    DEBUG = "Debug mode"
    DARK = "Dark mode"
    COMMAND = "Command poll (seconds)"
    GRAPH = "Graph update (seconds)"
    MESSAGE = "Message"
    SAVE = "Save"
    LIBS = "Libs"

    @property
    def name(self) -> str:
        return self.value
