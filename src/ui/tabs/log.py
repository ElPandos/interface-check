import asyncio
from datetime import UTC, datetime as dt
from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.enums.log_level import LogLevel
from src.ui.tabs.base import BasePanel, BaseTab

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


class LogPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config | None = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ) -> None:
        BasePanel.__init__(self, NAME, LABEL, LogTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._log_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base(LABEL)
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str) -> None:
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._log_screens:
                self._log_screens[screen_num] = LogContent(self._ssh_connection, self._host_handler, self._config)

            log_content = self._log_screens[screen_num]
            log_content.build(screen_num)


class LogContent:
    _MAX_LINES: int = 500

    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._log_component: ui.log | None = None
        self._buttons: dict[str, ui.button] = {}

    def build(self, screen_num: int) -> None:
        """Build log interface for the screen."""
        # Connection selector if available
        if self._host_handler:
            try:
                from src.ui.components.selector import Selector

                Selector(
                    getattr(self._host_handler, "_connect_route", {}),
                    getattr(self._host_handler, "_routes", {}),
                    self._on_connection_change,
                ).build()
            except ImportError:
                pass

        # Control buttons
        with ui.row().classes("w-full gap-2 mt-2 flex-wrap"):
            self._buttons["clear"] = ui.button(
                icon="cleaning_services", text="Clear", on_click=self._clear_log
            ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs")
            self._buttons["debug"] = ui.button(icon="bug_report", text="Debug", on_click=self._debug_log).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
            )
            self._buttons["remote"] = ui.button(
                icon="terminal", text="Remote", on_click=self._run_remote_async
            ).classes("bg-blue-300 hover:bg-blue-400 text-blue-900 px-2 py-1 text-xs")
            self._buttons["settings"] = ui.button(
                icon="settings", text="Settings", on_click=self._dump_settings
            ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs")
            ui.space()
            self._buttons["save"] = ui.button(icon="save", text="Save", on_click=self._save_log).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-2 py-1 text-xs"
            )

        self._update_button_states()

        # Log component
        self._log_component = ui.log(max_lines=self._MAX_LINES).classes("w-full h-64 overflow-auto p-2 bg-gray-100")

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        return self._ssh_connection is not None and self._ssh_connection.is_connected()

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        if remote_btn := self._buttons.get("remote"):
            if self._is_connected():
                remote_btn.enable()
            else:
                remote_btn.disable()

    def _run_remote_async(self) -> None:
        """Wrapper to run remote command asynchronously."""
        asyncio.create_task(self._run_remote())

    def _log(self, text: str, level: LogLevel) -> None:
        """Unified logging method."""
        if self._log_component:
            timestamp = dt.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
            formatted_text = f"{timestamp} [{level.name}] - {text}"
            self._log_component.push(formatted_text, classes=level.color)

    def _time(self) -> str:
        return dt.now(UTC).strftime("%Y-%m-%d %H:%M:%S")

    def _log_text(self, text: str, level: LogLevel) -> str:
        return f"{self._time()} [{level.name}] - {text}"

    def _debug_log(self) -> None:
        text = "Test"
        self.debug(text)
        self.info(text)
        self.warning(text)
        self.error(text)
        self.critical(text)

    async def _run_remote(self) -> None:
        if not self._is_connected():
            ui.notify("Not connected", color="warning")
            return

        async def get_text_input(_prompt: str) -> str | None:
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

        out, err = self._ssh_connection.exec_command(command, 10)
        self.debug(f"STDOUT: {out}")
        self.debug(f"STDERR: {err}")

    def _dump_settings(self) -> None:
        if self._config:
            self.debug(f"Dump settings: {self._config.model_dump_json()}")
        else:
            self.debug("No configuration available")

    def debug(self, text: str) -> None:
        self._log(text, LogLevel.DEBUG)

    def info(self, text: str) -> None:
        self._log(text, LogLevel.INFO)

    def warning(self, text: str) -> None:
        self._log(text, LogLevel.WARNING)

    def error(self, text: str) -> None:
        self._log(text, LogLevel.ERROR)

    def critical(self, text: str) -> None:
        self._log(text, LogLevel.CRITICAL)

    def _clear_log(self) -> None:
        if self._log_component:
            self._log_component.clear()

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id
        self._update_button_states()

    def _save_log(self) -> None:
        """Save log contents to file."""
        try:
            if not self._log_component:
                ui.notify("No log available", color="warning")
                return

            log_content = "\n".join(list(self._log_component.content))

            if not log_content.strip():
                ui.notify("No log content to save", color="warning")
                return

            timestamp = dt.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"interface_check_log_{timestamp}.txt"

            ui.download(log_content.encode(), filename)
            ui.notify(f"Log saved as {filename}", color="positive")

        except Exception as e:
            ui.notify(f"Failed to save log: {e!s}", color="negative")
