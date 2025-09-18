from annotated_types import T
from nicegui import ui

from src.ui.tabs.base_tab import BaseTab


class Host(BaseTab):
    __connected: bool

    def __init__(self) -> None:
        super().__init__()
        self.connected = False

    def __connect() -> None:
        pass

    def is_connected(self) -> bool:
        return self.__connected

    def build(self, title: str) -> None:
        super()._title(title)

        with ui.column().classes("w-full lp-10"):
            with ui.card().classes("w-full items-left"):
                with ui.row().classes("w-full lp-10"):
                    ui.input(placeholder="IP remote host").props("outlined dense")
                    ui.input(placeholder="Username").props("outlined dense")
                    ui.input(placeholder="Password").props("outlined dense")
            with ui.card().classes("w-full items-left"):
                with ui.row().classes("w-full lp-10"):
                    ui.input(placeholder="IP jump host").props("outlined dense")
                    ui.input(placeholder="Username").props("outlined dense")
                    ui.input(placeholder="Password").props("outlined dense")
            ui.button("Connect", on_click=self.__connect)

        with ui.card().classes("w-full items-left"):
            pass
