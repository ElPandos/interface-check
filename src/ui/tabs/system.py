"""System tab implementation."""

from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
from src.ui.components.selector import Selector
from src.ui.tabs.base import BasePanel, BaseTab

NAME = "system"
LABEL = "System"


class SystemTab(BaseTab):
    ICON_NAME: str = "computer"

    def __init__(self, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class SystemPanel(BasePanel, MultiScreen):
    def __init__(
        self,
        build: bool = False,
        config: Config = None,
        ssh_connection: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, SystemTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._config = config
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._icon = icon
        self._system_screens: dict[int, Any] = {}

        if build:
            self.build()

    def build(self):
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_control_base("System")
            self._build_content_base()

    def _build_screen(self, screen_num: int, classes: str):
        with (
            ui.card().classes(classes),
            ui.expansion(f"Host {screen_num}", icon="computer", value=True).classes("w-full"),
        ):
            if screen_num not in self._system_screens:
                self._system_screens[screen_num] = SystemContent(self._ssh_connection, self._host_handler, self._config)

            system_content = self._system_screens[screen_num]
            system_content.build(screen_num)


class SystemContent:
    def __init__(
        self, ssh_connection: SshConnection | None = None, host_handler: Any = None, config: Config | None = None
    ) -> None:
        self._ssh_connection = ssh_connection
        self._host_handler = host_handler
        self._config = config
        self._selected_connection: str | None = None
        self._system_info_container: ui.column | None = None
        self._buttons: dict[str, ui.button] = {}

    def build(self, screen_num: int) -> None:
        """Build system interface for the screen."""
        # Connection selector
        if self._host_handler:
            # TODO: Implement proper connection selector with SelectionProvider
            ui.label("Connection selector placeholder").classes("text-gray-500")

        # System controls
        with ui.row().classes("w-full gap-2 mt-2 flex-wrap"):
            self._buttons["system"] = ui.button("System Info", icon="info", on_click=self._get_system_info).classes(
                "bg-green-500 hover:bg-green-600 text-white"
            )

            self._buttons["cpu"] = ui.button("CPU Info", icon="memory", on_click=self._get_cpu_info).classes(
                "bg-blue-500 hover:bg-blue-600 text-white"
            )

            self._buttons["memory"] = ui.button("Memory Info", icon="storage", on_click=self._get_memory_info).classes(
                "bg-purple-500 hover:bg-purple-600 text-white"
            )

            self._buttons["clear"] = ui.button("Clear", icon="clear", on_click=self._clear_info).classes(
                "bg-gray-500 hover:bg-gray-600 text-white"
            )

        # System information display
        with ui.column().classes("w-full mt-4"):
            ui.label("System Information").classes("text-lg font-bold")
            self._system_info_container = ui.column().classes("w-full gap-2")
            self._show_empty_state()

        self._update_button_states()

    def _on_connection_change(self, connection_id: str | None) -> None:
        """Handle connection selection change."""
        self._selected_connection = connection_id
        self._update_button_states()

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        return self._ssh_connection is not None and self._ssh_connection.is_connected()

    def _update_button_states(self) -> None:
        """Update button states based on connection status."""
        is_connected = self._is_connected()
        for button_name in ("system", "cpu", "memory"):
            if button := self._buttons.get(button_name):
                if is_connected:
                    button.enable()
                else:
                    button.disable()

    def _show_empty_state(self) -> None:
        """Show empty state in results area."""
        if self._system_info_container:
            with self._system_info_container:
                ui.label("No system information retrieved yet").classes("text-gray-500 italic")

    def _execute_command(self, cmd: str, timeout: int = 5) -> tuple[str, str]:
        """Execute SSH command with error handling."""
        try:
            return self._ssh_connection.exec_command(cmd, timeout=timeout)
        except Exception:
            return "", "Command execution failed"

    def _get_system_info(self) -> None:
        """Get general system information."""
        if not self._is_connected() or not self._system_info_container:
            ui.notify("SSH connection required", color="negative")
            return

        commands = [
            ("uname -a", "System"),
            ("uptime", "Uptime"),
            ("whoami", "Current User"),
            ("pwd", "Current Directory"),
        ]

        with self._system_info_container:
            with ui.card().classes("w-full p-4 border"):
                ui.label("General System Information").classes("font-bold text-green-600 mb-2")

                for cmd, label in commands:
                    stdout, stderr = self._execute_command(cmd)
                    if stdout:
                        ui.label(f"{label}: {stdout.strip()}").classes("text-sm")
                    elif stderr:
                        ui.label(f"{label}: Error - {stderr.strip()}").classes("text-sm text-red-600")

        ui.notify("System information retrieved", color="positive")

    def _get_cpu_info(self) -> None:
        """Get CPU information."""
        if not self._is_connected() or not self._system_info_container:
            ui.notify("SSH connection required", color="negative")
            return

        stdout, stderr = self._execute_command("cat /proc/cpuinfo | head -20")

        with self._system_info_container:
            with ui.card().classes("w-full p-4 border"):
                ui.label("CPU Information").classes("font-bold text-blue-600 mb-2")
                if stdout:
                    ui.code(stdout).classes("text-xs")
                elif stderr:
                    ui.label(f"Error: {stderr}").classes("text-sm text-red-600")

        ui.notify("CPU information retrieved", color="positive")

    def _get_memory_info(self) -> None:
        """Get memory information."""
        if not self._is_connected() or not self._system_info_container:
            ui.notify("SSH connection required", color="negative")
            return

        commands = [("free -h", "Memory Usage"), ("df -h", "Disk Usage")]

        with self._system_info_container:
            with ui.card().classes("w-full p-4 border"):
                ui.label("Memory & Storage Information").classes("font-bold text-purple-600 mb-2")

                for cmd, label in commands:
                    stdout, stderr = self._execute_command(cmd)
                    if stdout:
                        ui.label(label).classes("font-semibold text-sm mt-2")
                        ui.code(stdout).classes("text-xs")
                    elif stderr:
                        ui.label(f"{label}: Error - {stderr}").classes("text-sm text-red-600")

        ui.notify("Memory information retrieved", color="positive")

    def _clear_info(self) -> None:
        """Clear system information display."""
        if self._system_info_container:
            self._system_info_container.clear()
            self._show_empty_state()
        ui.notify("System information cleared", color="info")
