import asyncio
from datetime import UTC, datetime as dt
from typing import TYPE_CHECKING

from nicegui import ui

from src.models.configurations import AppConfig
from src.ui.enums.log_level import LogLevel
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.connect import Ssh

if TYPE_CHECKING:
    from nicegui.elements.log import Log

try:
    from src.ui.components.selector import Selector
except ImportError:
    Selector = None

NAME = "log"
LABEL = "Log"


class LogTab(BaseTab):
    ICON_NAME: str = "article"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class LogPanel(BasePanel):
    _MAX_LINES: int = 500

    def __init__(
        self,
        build: bool = False,
        app_config: AppConfig | None = None,
        ssh: Ssh | None = None,
        host_handler=None,
        icon: ui.icon | None = None,
    ) -> None:
        super().__init__(NAME, LABEL, "article")

        self._app_config = app_config
        self._ssh = ssh
        self._host_handler = host_handler
        self._icon = icon
        self._selected_connection = None
        self.num_screens = 1
        self.screen_connections: dict[int, str] = {}
        self._logs: dict[int, Log] = {}

        if build:
            self.build()

    def _time(self) -> str:
        return dt.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    def _log_text(self, text: str, level: LogLevel) -> str:
        return f"{self._time()} [{level.name}] - {text}"

    def _debug_log(self, screen_num: int = 1) -> None:
        text = "Test"
        self.debug(text, screen_num)
        self.info(text, screen_num)
        self.warning(text, screen_num)
        self.error(text, screen_num)
        self.critical(text, screen_num)

    async def _run_remote(self) -> None:
        if (
            self._selected_connection is not None
            and self._host_handler
            and self._selected_connection in getattr(self._host_handler, "_connect_route", {})
        ):

            async def get_text_input(prompt: str) -> str | None:
                """Show a dialog with a text input and return the user's input."""
                future = asyncio.get_event_loop().create_future()
                dialog = ui.dialog()

                with dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
                    ui.label("Remote Command").classes("text-xl font-bold mb-6 text-center text-gray-800")

                    with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                        ui.label("Command details").classes("font-semibold mb-3 text-gray-700")
                        input_field = ui.input("Command", placeholder="ls -la").classes("w-full")
                        input_field.props("outlined").tooltip("Enter the command to execute on remote host")

                    with ui.row().classes("w-full mt-6"):
                        ui.button(
                            icon="play_arrow",
                            text="Execute",
                            on_click=lambda: (dialog.close(), future.set_result(input_field.value)),
                        ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg")
                        ui.space()
                        ui.button(
                            icon="cancel", text="Cancel", on_click=lambda: (dialog.close(), future.set_result(None))
                        ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg")

                dialog.open()
                return await future

            command = await get_text_input("Enter command:")
            if not command:
                ui.notify("Command cancelled", color="info")
                return

            out, err = self._ssh.exec_command(command, 10)
            self.debug(f"STDOUT: {out}")
            self.debug(f"STDERR: {err}")
        else:
            ui.notify("Not connected", color="warning")

    def _dump_settings(self) -> None:
        self.debug(f"Dump settings: {self._app_config.model_dump_json()}")

    def debug(self, text: str, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].push(self._log_text(text, LogLevel.DEBUG), classes=LogLevel.DEBUG.color)

    def info(self, text: str, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].push(self._log_text(text, LogLevel.INFO), classes=LogLevel.INFO.color)

    def warning(self, text: str, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].push(self._log_text(text, LogLevel.WARNING), classes=LogLevel.WARNING.color)

    def error(self, text: str, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].push(self._log_text(text, LogLevel.ERROR), classes=LogLevel.ERROR.color)

    def critical(self, text: str, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].push(self._log_text(text, LogLevel.CRITICAL), classes=LogLevel.CRITICAL.color)

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_controls()
            self._build_content()

    def _build_controls(self) -> None:
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            if self._icon_name:
                ui.icon(self._icon_name, size="lg").classes("text-blue-600")
            ui.label("Log").classes("text-lg font-bold")
            ui.space()
            ui.select([1, 2, 3, 4], value=1, label="Hosts").classes("w-32").on_value_change(self._on_screen_change)

    def _build_content(self) -> None:
        with ui.column().classes("w-full h-full gap-4"):
            self.content_container = ui.column().classes("w-full")
            with self.content_container:
                self._render_screens()

    def _render_screens(self) -> None:
        self.content_container.clear()
        with self.content_container:
            if self.num_screens == 1:
                self._build_screen(1, "w-full")
            elif self.num_screens == 2:
                with ui.row().classes("w-full gap-2"):
                    self._build_screen(1, "flex-1")
                    self._build_screen(2, "flex-1")
            elif self.num_screens == 3:
                with ui.column().classes("w-full gap-2"):
                    with ui.row().classes("w-full gap-2"):
                        self._build_screen(1, "flex-1")
                        self._build_screen(2, "flex-1")
                    self._build_screen(3, "w-full")
            elif self.num_screens == 4:
                with ui.column().classes("w-full gap-2"):
                    with ui.row().classes("w-full gap-2"):
                        self._build_screen(1, "flex-1")
                        self._build_screen(2, "flex-1")
                    with ui.row().classes("w-full gap-2"):
                        self._build_screen(3, "flex-1")
                        self._build_screen(4, "flex-1")

    def _build_screen(self, screen_num: int, classes: str) -> None:
        with ui.card().classes(classes), ui.expansion(f"Host {screen_num}", icon="computer").classes("w-full"):
            if self._host_handler and Selector:
                Selector(
                    getattr(self._host_handler, "_connect_route", {}),
                    getattr(self._host_handler, "_routes", {}),
                    lambda conn_id, s=screen_num: self._on_connection_change(conn_id, s),
                ).build()

            with ui.row().classes("w-full gap-2 mt-2 flex-wrap"):
                ui.button(
                    icon="cleaning_services", text="Clear", on_click=lambda s=screen_num: self._clear_log(s)
                ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs")
                ui.button(icon="bug_report", text="Debug", on_click=lambda s=screen_num: self._debug_log(s)).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
                )
                ui.button(
                    icon="terminal", text="Remote", on_click=lambda s=screen_num: self._run_remote_for_host(s)
                ).classes("bg-blue-300 hover:bg-blue-400 text-blue-900 px-2 py-1 text-xs")
                ui.button(icon="settings", text="Settings", on_click=self._dump_settings).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
                )
                ui.space()
                ui.button(icon="save", text="Save", on_click=lambda s=screen_num: self._save_log(s)).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
                )

            # Log component outside expansion
            self._logs[screen_num] = ui.log(max_lines=self._MAX_LINES).classes(
                "w-full h-64 overflow-auto p-2 bg-gray-100"
            )

    def _clear_log(self, screen_num: int = 1) -> None:
        if screen_num in self._logs:
            self._logs[screen_num].clear()

    def _on_connection_change(self, connection_id: str | None, screen_num: int | None = None) -> None:
        """Handle connection selection change."""
        if screen_num is not None:
            self.screen_connections[screen_num] = connection_id
            self._update_icon_status()
        else:
            self._selected_connection = connection_id

    def _on_screen_change(self, e) -> None:
        self.num_screens = e.value
        self._render_screens()
        self._update_icon_status()

    def _update_icon_status(self) -> None:
        pass

    def _run_remote_for_host(self, screen_num: int) -> None:
        """Run remote command for specific host."""
        if screen_num in self.screen_connections:
            self._selected_connection = self.screen_connections[screen_num]
            _task = asyncio.create_task(self._run_remote())
        else:
            ui.notify(f"No connection selected for Host {screen_num}", color="warning")

    def _save_log(self, screen_num: int = 1) -> None:
        """Save log contents to file."""
        try:
            if screen_num not in self._logs:
                ui.notify("No log available for this screen", color="warning")
                return

            log_content = "\n".join(list(self._logs[screen_num].content))

            if not log_content.strip():
                ui.notify("No log content to save", color="warning")
                return

            timestamp = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"interface_check_log_host{screen_num}_{timestamp}.txt"

            ui.download(log_content.encode(), filename)
            ui.notify(f"Log saved as {filename}", color="positive")

        except Exception as e:
            ui.notify(f"Failed to save log: {e!s}", color="negative")
