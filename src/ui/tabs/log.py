from datetime import datetime as dt

from nicegui import ui
from nicegui.elements.log import Log

from src.models.configurations import AppConfig
from src.ui.enums.log_level import LogLevel
from src.ui.tabs.base import BasePanel, BaseTab
from src.utils.ssh_connection import SshConnection

NAME = "log"
LABEL = "Log"


class LogTab(BaseTab):
    ICON_NAME: str = "logo_dev"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)

        if build:
            self.build()

    def build(self) -> None:
        super().build()


class LogPanel(BasePanel):
    _MAX_LINES: int = 500
    _log: Log

    def __init__(self, build: bool = False, app_config: AppConfig = None, ssh_connection: SshConnection = None):
        super().__init__(NAME, LABEL)

        self._app_config = app_config
        self.ssh_connection = ssh_connection

        if build:
            self.build()

    def _time(self) -> str:
        return dt.now().strftime("%Y-%m-%d %H:%M:%S")

    def _log_text(self, text: str, level: LogLevel) -> str:
        return f"{self._time()} [{level.name}] - {text}"

    def _debug_log(self) -> None:
        text = "Test"
        self.debug(text)
        self.info(text)
        self.warning(text)
        self.error(text)
        self.critical(text)

    def _run_remote(self) -> None:
        if self.ssh_connection.is_connected():
            out, err = self.ssh_connection.exec_command("ip addr", 10)
            self.debug(f"STDOUT: {out}")
            self.debug(f"STDERR: {err}")
        else:
            ui.notify("Not connected", color="warning")

    def _dump_settings(self) -> None:
        self.debug(f"Dump settings: {self._app_config.model_dump_json()}")

    def debug(self, text: str) -> None:
        if self._log is not None:
            self._log.push(self._log_text(text, LogLevel.DEBUG), classes=LogLevel.DEBUG.color)

    def info(self, text: str) -> None:
        if self._log is not None:
            self._log.push(self._log_text(text, LogLevel.INFO), classes=LogLevel.INFO.color)

    def warning(self, text: str) -> None:
        if self._log is not None:
            self._log.push(self._log_text(text, LogLevel.WARNING), classes=LogLevel.WARNING.color)

    def error(self, text: str) -> None:
        if self._log is not None:
            self._log.push(self._log_text(text, LogLevel.ERROR), classes=LogLevel.ERROR.color)

    def critical(self, text: str) -> None:
        if self._log is not None:
            self._log.push(self._log_text(text, LogLevel.CRITICAL), classes=LogLevel.CRITICAL.color)

    # @ui.refreshable
    def build(self) -> None:
        with ui.tab_panel(self.name):
            super().build()
            with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
                with ui.column().classes("w-full h-full flex flex-col"):
                    # Log (flexible, scrollable)
                    self._log = ui.log(max_lines=self._MAX_LINES).classes(
                        "w-full flex-grow overflow-auto p-5 bg-gray-200"
                    )

                    # Buttons (footer, fixed at bottom)
                    with ui.row().classes("w-full flex-none p-2 justify-start bg-white"):
                        ui.button("Clear log", on_click=self.clear)
                        ui.button("Debug - Log time", on_click=self._debug_log)
                        # ui.button(                           "Remote command",
                        #     on_click=lambda: threading.Thread(target=self._run_remote, daemon=True).start(),
                        # )
                        (ui.button("Remote command", on_click=self._run_remote),)
                        ui.button("Dump settings", on_click=self._dump_settings)

    # def refresh(self):
    #    self.build.refresh()

    def clear(self) -> None:
        self._log.clear()
