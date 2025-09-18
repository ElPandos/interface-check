from nicegui import ui


class BaseTab:
    __CONTENT_OF_STRING = "Content of -> "

    def __init__(self) -> None:
        pass

    def _title(self, title: str) -> None:
        ui.label(self.__CONTENT_OF_STRING + title)

    def build(self, title: str) -> None:
        self._title(title)

        names = ["Alice", "Bob", "Carol"]

        with ui.card().classes("w-full items-left"):
            with ui.column().classes("w-full items-left"):
                ui.select(names, multiple=True, value=names[:2], label="Interfaces").classes("w-64").props("use-chips")

        with ui.card().classes("w-full items-left"):
            pass
