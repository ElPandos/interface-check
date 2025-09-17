from nicegui import ui


class Mlxlink:
    def __init__(self) -> None:
        pass

    def build(self) -> None:
        # sudo mlxlink -d /dev/mst/mt4119_pciconf0 --port_type PCIE --show_eye

        names = ["Alice", "Bob", "Carol"]

        with ui.card().classes("w-full items-left"):
            with ui.column().classes("w-full items-left"):
                ui.select(names, multiple=True, value=names[:2], label="Interfaces").classes("w-64").props("use-chips")

        pass
