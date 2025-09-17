import threading
from datetime import datetime as dt
from typing import Any

import paramiko
from nicegui import ui
from nicegui.elements.log import Log

# from src.ui.handlers.settings import settings
from ..enums.log_level import LogLevel


class Log:
    """A UI log widget with colored log levels."""

    __MAX_LINES: int = 1000
    __log: Log

    def __init__(self) -> None:
        self.__log = None

    def __time(self) -> str:
        return dt.now().strftime("%Y-%m-%d %H:%M:%S")

    def __log_text(self, text: str, level: LogLevel) -> str:
        return f"{self.__time()} [{level.name}] - {text}"

    def __debug_log(self) -> None:
        text = "Test"
        self.debug(text)
        self.info(text)
        self.warning(text)
        self.error(text)
        self.critical(text)

    def __run_remote(self) -> None:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("137.58.231.134", username="emvekta", password="emvekta")

        stdin, stdout, stderr = ssh.exec_command("ls -la /tmp")
        stdin = stdin.read().decode()
        stdout = stdout.read().decode()
        stderr = stderr.read().decode()
        ssh.close()

        self.debug(f"Run remote - STDIN: {stdin}")
        self.debug(f"Run remote - STDOUT: {stdout}")
        self.debug(f"Run remote - STDERR: {stderr}")

    def __dump_settings(self) -> None:
        # self.debug(f"Dump settings: {settings.get_settings()}")
        pass

    def debug(self, text: str) -> None:
        if self.__log is not None:
            self.__log.push(self.__log_text(text, LogLevel.DEBUG), classes=LogLevel.DEBUG.color)

    def info(self, text: str) -> None:
        if self.__log is not None:
            self.__log.push(self.__log_text(text, LogLevel.INFO), classes=LogLevel.INFO.color)

    def warning(self, text: str) -> None:
        if self.__log is not None:
            self.__log.push(self.__log_text(text, LogLevel.WARNING), classes=LogLevel.WARNING.color)

    def error(self, text: str) -> None:
        if self.__log is not None:
            self.__log.push(self.__log_text(text, LogLevel.ERROR), classes=LogLevel.ERROR.color)

    def critical(self, text: str) -> None:
        if self.__log is not None:
            self.__log.push(self.__log_text(text, LogLevel.CRITICAL), classes=LogLevel.CRITICAL.color)

    def build(self) -> None:
        """Build the log UI with a button for testing."""
        ui.query("body").classes("h-screen m-0 p-0")
        with ui.column().classes("w-full h-full"):
            self.__log = ui.log(max_lines=self.__MAX_LINES).classes("w-full flex-grow")
            with ui.row().classes("w-full"):
                ui.button("Clear log", on_click=self.clear)
                ui.button("Debug - Log time", on_click=self.__debug_log)
                ui.button(
                    "Remote command",
                    on_click=lambda: threading.Thread(target=self.__run_remote, daemon=True).start(),
                )
                ui.button("Dump settings", on_click=self.__dump_settings)

    def clear(self) -> None:
        self.__log.clear()


# Create the global singleton instance
logger = Log()
