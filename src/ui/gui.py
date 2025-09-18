from typing import Any

from nicegui import ui

from src.utils.process_manager import ProcessManager
from src.ui.enums.tabs import Tabs
from src.ui.handlers.settings import settings
from src.ui.tabs.ethtool import Ethtool
from src.ui.tabs.host import Host
from src.ui.tabs.info import Info
from src.ui.tabs.log import Log, logger
from src.ui.tabs.mlxconfig import Mlxconfig
from src.ui.tabs.mlxlink import Mlxlink


class Gui:
    __log = Any

    def __init__(self) -> None:
        ui.query(".nicegui-content").classes("p-0 w-full")
        ui.query(".q-page").classes("flex")

        self.__header()
        self.__body()
        self.__right_drawer()
        self.__footer()
        self.__sticky_footer()

        ui.run()

    def __header(self) -> None:
        with ui.header().classes(replace="row items-center justify-between"):
            with ui.tabs() as self.tabs:
                for tab in Tabs:  # Enum
                    ui.tab(tab.name, icon=tab.icon)

            # Drawer button
            ui.button(on_click=lambda: self.right_drawer.toggle(), icon="settings").props("flat color=white")

    def __body(self) -> None:
        with ui.tab_panels(self.tabs, value=Tabs.HOST.name).classes("w-full h-fit bg-gray-100"):
            for tab in Tabs:  # Enum
                with ui.tab_panel(tab.name):
                    panel_instance = tab.create_panel()
                    panel_instance.build(tab.name)

    def __right_drawer(self) -> None:
        with ui.right_drawer().classes("bg-blue-100") as self.right_drawer:
            self.right_drawer.hide()  # Hide as default
            settings.build()

    def __footer(self) -> None:
        with ui.footer(value=False) as self.footer:
            pm = ProcessManager()
            proc = pm.run('git describe --all --long | cut -d "-" -f 3')
            stdout, stderr = pm.get_output(proc)
            logger.debug(f"Footer: STDOUT: {stdout}")
            logger.debug(f"Footer: STDERR: {stderr}")

            with ui.row().classes("w-full items-center"):
                ui.add_head_html(
                    '<link href="https://unpkg.com/eva-icons@1.1.3/style/eva-icons.css" rel="stylesheet" />'
                )
                ui.icon("eva-github").classes("text-4xl items-center")
                ui.label(f" Patchset: {stdout}")
                ui.separator()

    def __sticky_footer(self) -> None:
        with ui.page_sticky(position="bottom-right", x_offset=20, y_offset=20):
            ui.button(on_click=self.footer.toggle, icon="build_circle").props("fab")
