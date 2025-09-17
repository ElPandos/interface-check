from nicegui import ui


class Mlxconfig:
    def __init__(self) -> None:
        pass

    def build(self) -> None:
        # sudo mlxconfig -d /dev/mst/mt4119_pciconf0 query

        names = ["Alice", "Bob", "Carol"]

        with ui.card().classes("w-full items-left"):
            with ui.column().classes("w-full items-left"):
                ui.select(names, multiple=True, value=names[:2], label="Interfaces").classes("w-64").props("use-chips")

        pass
