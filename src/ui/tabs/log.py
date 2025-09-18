import threading
from datetime import datetime as dt
from typing import Any

import paramiko
from nicegui import ui
from nicegui.elements.log import Log

from src.ui.tabs.base_tab import BaseTab

from ..enums.log_level import LogLevel


class Log(BaseTab):
    __MAX_LINES: int = 500
    __log: Log

    def __init__(self) -> None:
        """A UI log widget with colored log levels."""
        super().__init__()
        self.__log = None

    def build(self, title: str) -> None:
        super.build(title)

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
        # ---------- SSH Jumphost ----------
        jump_host = "137.58.231.134"
        jump_user = "emvekta"
        jump_pass = "emvekta"

        # ---------- Final Target ----------
        target_host = "172.16.87.1"
        target_user = "emvekta"
        target_pass = "emvekta"

        # Connect to jumphost first
        jump_ssh = paramiko.SSHClient()
        jump_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        jump_ssh.connect(
            jump_host,
            username=jump_user,
            password=jump_pass,
            look_for_keys=False,
            allow_agent=False,
        )

        # Open a channel from jumphost -> target
        jump_transport = jump_ssh.get_transport()
        dest_addr = (target_host, 22)
        local_addr = (jump_host, 22)
        channel = jump_transport.open_channel("direct-tcpip", dest_addr, local_addr)

        # Connect to the final target through that channel
        target_ssh = paramiko.SSHClient()
        target_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        target_ssh.connect(
            target_host,
            username=target_user,
            password=target_pass,
            sock=channel,  # <--- magic happens here
            look_for_keys=False,
            allow_agent=False,
        )

        # Run your command on the target host
        stdin, stdout, stderr = target_ssh.exec_command("ip addr")
        stdout_str = stdout.read().decode()
        stderr_str = stderr.read().decode()

        target_ssh.close()
        jump_ssh.close()

        self.debug(f"Run remote - STDOUT: {stdout_str}")
        self.debug(f"Run remote - STDERR: {stderr_str}")

    def __dump_settings(self) -> None:
        from src.ui.handlers.settings import settings

        self.debug(f"Dump settings: {settings.get_settings()}")
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

    def build(self, title: str) -> None:
        """Build the log UI with buttons fixed at the bottom."""
        with ui.column().classes("w-full h-full flex flex-col"):
            ui.label(title)

            # Log (flexible, scrollable)
            self.__log = ui.log(max_lines=self.__MAX_LINES).classes("w-full flex-grow overflow-auto p-5 bg-gray-200")

            # Buttons (footer, fixed at bottom)
            with ui.row().classes("w-full flex-none p-2 justify-start border-t border-gray-300 bg-white"):
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
