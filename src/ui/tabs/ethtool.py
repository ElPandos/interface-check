from nicegui import ui


class Ethtool:
    def __init__(self) -> None:
        pass

    def build(self) -> None:
        names = ["Alice", "Bob", "Carol"]

        with ui.card().classes("w-full items-left"):
            with ui.column().classes("w-full items-left"):
                ui.select(names, multiple=True, value=names[:2], label="Interfaces").classes("w-64").props("use-chips")
