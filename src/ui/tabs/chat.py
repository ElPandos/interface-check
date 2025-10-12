from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.connect import Ssh

NAME = "chat"
LABEL = "Chat"


class ChatTab(BaseTab):
    ICON_NAME: str = "tips_and_updates"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class ChatPanel(BasePanel):
    def __init__(self, _build=False, app_config: AppConfig = None, ssh: Ssh = None):
        super().__init__(NAME, LABEL, ChatTab.ICON_NAME)
        self._app_config = app_config
        self._ssh = ssh

        # if build:
        #    self.build()

    def build(self):
        with ui.tab_panel(self._name):
            # Build tab info
            super().build()

            # Build chat window
            self._build_chat()

            # Build input field
            self._build_input()

    def _build_chat(self) -> None:
        with ui.card().classes("w-full"):
            pass

    def _build_input(self) -> None:
        with ui.card().classes("w-full"):
            pass
