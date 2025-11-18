import logging

from nicegui import ui

from src.platform.enums.log import LogName

logger = logging.getLogger(LogName.MAIN.value)

from src.core.connect import SshConnection
from src.core.worker import Worker, WorkManager
from src.models.config import Config
from src.platform.bak.commands import Common, Ethtool, Modify, System
from src.ui.handlers.graph import GraphHandler
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "ethtool"
LABEL = "Ethtool"


class EthtoolTab(BaseTab):
    ICON_NAME: str = "home_repair_service"

    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class EthtoolPanel(BasePanel):
    _work_manager: WorkManager

    def __init__(
        self,
        *,
        build: bool = False,
        cfg: Config = None,
        ssh: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        super().__init__(NAME, LABEL, EthtoolTab.ICON_NAME)
        self._cfg = cfg
        self._ssh = ssh
        self._host_handler = host_handler
        self._icon = icon
        self._work_manager = WorkManager()
        self.num_screens = 1
        self.screen_connections = {}
        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_controls()
            self._build_content()
            if self._icon:
                self._icon.style("color: #ef4444")

    def _close_card(
        self, card: ui.card, _interface: str | None = None, kill_worker: bool = False
    ) -> None:
        if kill_worker:
            logger.debug("Kill worker")
            self._work_manager.reset()
        card.delete()
        logger.debug("Card deleted")

    def _build_controls(self) -> None:
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.label("Ethtool").classes("text-lg font-bold")
            ui.space()
            ui.select([1, 2, 3, 4], value=1, label="Hosts").classes("w-32").on_value_change(
                self._on_screen_change
            )

    def _build_content(self) -> None:
        self.content_container = ui.column().classes("w-full h-full")
        with self.content_container:
            self._render_screens()

    def _render_screens(self):
        self.content_container.clear()
        with self.content_container:
            if self.num_screens == 1:
                self._build_screen(1, "w-full h-full")
            elif self.num_screens == 2:
                with ui.row().classes("w-full h-full gap-2"):
                    self._build_screen(1, "flex-1 h-full")
                    self._build_screen(2, "flex-1 h-full")
            elif self.num_screens == 3:
                with ui.column().classes("w-full h-full gap-2"):
                    with ui.row().classes("w-full flex-1 gap-2"):
                        self._build_screen(1, "flex-1 h-full")
                        self._build_screen(2, "flex-1 h-full")
                    self._build_screen(3, "w-full flex-1")
            elif self.num_screens == 4:
                with ui.column().classes("w-full h-full gap-2"):
                    with ui.row().classes("w-full flex-1 gap-2"):
                        self._build_screen(1, "flex-1 h-full")
                        self._build_screen(2, "flex-1 h-full")
                    with ui.row().classes("w-full flex-1 gap-2"):
                        self._build_screen(3, "flex-1 h-full")
                        self._build_screen(4, "flex-1 h-full")

    def _build_screen(self, screen_num, classes):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer").classes("w-full"),
        ):
            if self._host_handler:
                # TODO: Implement proper connection selector with SelectionProvider
                ui.label("Connection selector placeholder").classes("text-gray-500")
            ui.button(
                "Scan Interfaces", on_click=lambda s=screen_num: self._scan_interfaces_for_screen(s)
            ).classes("bg-red-300 hover:bg-red-400 text-red-900 mt-2")
            ui.label(f"Content for host {screen_num}").classes("mt-4")

    def _on_screen_change(self, e):
        self.num_screens = e.value
        self._render_screens()
        self._update_icon_status()

    def _on_connection_change(self, connection_id, screen_num):
        if not hasattr(self, "screen_connections"):
            self.screen_connections = {}
        self.screen_connections[screen_num] = connection_id
        self._update_icon_status()

    def _update_icon_status(self):
        if (
            hasattr(self, "screen_connections")
            and any(self.screen_connections.values())
            and self._icon
        ):
            self._icon.style("color: #10b981")
        elif self._icon:
            self._icon.style("color: #ef4444")

    def _scan_interfaces_for_screen(self, screen_num):
        ui.notify(f"Scanning interfaces for screen {screen_num}", color="info")
        self._scan_interfaces()

    def _scan_interfaces(self):
        if not self._ssh:
            logger.warning("No SSH connection object")
            return

        if not self._ssh.is_connected():
            logger.warning("No SSH connection established")
            return

        _, err = self._ssh.exec_command(System().install_psutil().syntax)
        if err:
            logger.warning("Failed to install python library: psutil")
            return

        out, err = self._ssh.exec_command(Common().get_interfaces().syntax)
        if err:
            logger.warning("Failed to collect host interface names")
            return

        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
            selection = (
                ui.select(
                    Modify().to_list(out),
                    multiple=True,
                    value=None,
                    label="Interfaces",
                )
                .classes("w-40")
                .classes("w-64")
                .props("use-chips")
            )

            ui.button("Start", on_click=lambda opt=selection: self._activate_workers(opt))
            ui.space()
            ui.button("X", on_click=lambda opt=card: self._close_card(opt, kill_worker=True))

    def _activate_workers(self, options: list) -> None:
        for interface in options.value:
            self._work_manager.add(
                Worker(Ethtool().module_info(interface), interface, self._cfg, self._ssh)
            )
            self._build_source(interface)

    def _build_source(self, interface: str) -> None:
        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
            sample = self._work_manager.get_worker(interface).get_first_sample()
            selection = (
                ui.select(
                    list(sample.snapshot.keys()),
                    multiple=True,
                    value=None,
                    label="Source",
                )
                .classes("w-40")
                .classes("w-64")
                .props("use-chips")
            )
            ui.button("Start", on_click=lambda opt=selection: self._activate_source(interface, opt))
            ui.space()
            ui.button(
                "X", on_click=lambda opt=card: self._close_card(opt, interface, kill_worker=True)
            )

    def _activate_source(self, interface: str, options: list) -> None:
        for source in options.value:
            self._build_value(interface, source)

    def _build_value(self, interface: str, source: str) -> None:
        card = ui.card().classes("w-full")
        with card, ui.row().classes("w-full"):
            samples = self._work_manager.get_worker(interface).get_all_samples()
            selection = (
                ui.select(
                    list(samples[0].snapshot[source].keys()),
                    multiple=True,
                    value=None,
                    label="value",
                )
                .classes("w-40")
                .classes("w-64")
                .props("use-chips")
            )
            ui.button(
                "Start", on_click=lambda opt=selection: self._plot_values(interface, source, opt)
            )
            ui.space()
            ui.button("X", on_click=lambda opt=card: self._close_card(opt))

    def _plot_values(self, interface: str, source: str, options: list) -> None:
        gh = GraphHandler()
        for value in options.value:
            gh.add(self._work_manager, self._cfg, interface, source, value)
