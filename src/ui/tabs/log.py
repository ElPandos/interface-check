import threading
from datetime import datetime as dt

import paramiko
from nicegui import ui
from nicegui.elements.log import Log

from src.models.configurations import AppConfig
from src.ui.tabs.base import BasePanel, BaseTab

from src.ui.enums.log_level import LogLevel
from src.utils.ssh_connection import SshConnection


class LogTab(BaseTab):

    def __init__(self, app_config: AppConfig) -> None:
        super().__init__(app_config)

        self._name = "log"
        self._label = "Log"
        self._icon_name = "logo_dev"

        self._build()

    def _build(self) -> None:
        super()._build()


class LogPanel(BasePanel):
    _MAX_LINES: int = 500
    _log: Log

    def __init__(self, app_config: AppConfig, ssh_connection: SshConnection = None):
        super().__init__(app_config, ssh_connection)

        self._name = "log"
        self._label = "Log"

        self._build()

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
        out, err = self.get_ssh().exec_command("ip addr", 10)
        self.debug(f"STDOUT: {out}")
        self.debug(f"STDERR: {err}")

    def _dump_settings(self) -> None:
        from src.ui.handlers.settings import settings
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

    def _build(self) -> None:
        with ui.tab_panel(self._name):
            super()._build()
            with ui.card().classes("w-full items-left"), ui.column().classes("w-full items-left"):
                with ui.column().classes("w-full h-full flex flex-col"):

                    # Log (flexible, scrollable)
                    self._log = ui.log(max_lines=self._MAX_LINES).classes("w-full flex-grow overflow-auto p-5 bg-gray-200")

                    # Buttons (footer, fixed at bottom)
                    with ui.row().classes("w-full flex-none p-2 justify-start bg-white"):
                        ui.button("Clear log", on_click=self.clear)
                        ui.button("Debug - Log time", on_click=self._debug_log)
                        # ui.button(                           "Remote command",
                        #     on_click=lambda: threading.Thread(target=self._run_remote, daemon=True).start(),
                        # )
                        ui.button("Remote command", on_click=self._run_remote),
                        ui.button("Dump settings", on_click=self._dump_settings)

    def clear(self) -> None:
        self._log.clear()
