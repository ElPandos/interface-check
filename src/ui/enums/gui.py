from enum import Enum


class Option(Enum):
    SWITCH = "Switch"
    SLIDER = "Slider"
    TEXT = "Text"
    BUTTON = "Button"
    INFO = "Info"

    @property
    def name(self) -> str:
        return self.value
