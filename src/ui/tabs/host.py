from nicegui import ui


class Host:
    connected: bool

    def __init__(self) -> None:
        self.connected = False

    def __connect() -> None:
        pass

    def build(self) -> None:
        # Add version and other system info for the main program here

        # IP connected host
        # System information
        # NIC info
        #

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
