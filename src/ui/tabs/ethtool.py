from nicegui import ui

from src.ui.tabs.base_tab import BaseTab


class Ethtool(BaseTab):
    def __init__(self) -> None:
        super().__init__()
        pass

    def build(self, title: str) -> None:
        super().build(title)
