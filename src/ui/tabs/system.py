"""System tab implementation."""

from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.core.screen import MultiScreen
from src.models.config import Config
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
        cfg: Config = None,
        ssh: SshConnection = None,
        host_handler=None,
        icon: ui.icon = None,
    ):
        BasePanel.__init__(self, NAME, LABEL, SystemTab.ICON_NAME)
        MultiScreen.__init__(self)

        self._cfg = cfg
        self._ssh = ssh
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
        with ui.card().classes(classes):
            # Card header with route selector
            with ui.row().classes("w-full items-center gap-2 p-4 border-b"):
                ui.icon("computer", size="md").classes("text-blue-600")
                ui.label(f"Host {screen_num}").classes("text-lg font-semibold")
                ui.space()

                if screen_num not in self._system_screens:
                    self._system_screens[screen_num] = SystemContent(
                        None, self._host_handler, self._cfg, self, screen_num
                    )

                # Route selector in header
                system_content = self._system_screens[screen_num]
                system_content.build_route_selector()

            # Content area
            with ui.column().classes("w-full p-4"):
                system_content.build_content(screen_num)


class SystemContent:
    def __init__(
        self,
        ssh: SshConnection | None = None,
        host_handler: Any = None,
        cfg: Config | None = None,
        parent_panel: SystemPanel | None = None,
        screen_num: int = 1,
    ) -> None:
        self._ssh = ssh
        self._host_handler = host_handler
        self._cfg = cfg
        self._parent_panel = parent_panel
        self._screen_num = screen_num
        self._selected_route: int | None = None
        self._system_info_container: ui.column | None = None
        self._buttons: dict[str, ui.button] = {}
        self._route_selector: ui.select | None = None

    def build_route_selector(self) -> None:
        """Build route selector in card header."""
        self._route_selector = (
            ui.select(options=[], value=None, label="Connected Routes")
            .classes("w-64")
            .on_value_change(self._on_route_change)
        )
        ui.timer(0.5, self._update_route_options, active=True)

    def build_content(self, screen_num: int) -> None:
        """Build system interface for the screen."""
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

    def _on_route_change(self, e: Any) -> None:
        """Handle route selection change."""
        if hasattr(e, "value") and e.value is not None:
            self._selected_route = getattr(self, "_route_value_map", {}).get(e.value)
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, self._selected_route)
        else:
            self._selected_route = None
            if self._parent_panel:
                self._parent_panel.set_screen_route(self._screen_num, None)
        self._update_button_states()

    def _update_route_options(self) -> None:
        """Update route selector options."""
        if not (self._parent_panel and self._route_selector):
            return

        connected_routes = self._parent_panel.get_connected_route_options()
        if not connected_routes:
            self._route_selector.options = []
            self._route_selector.update()
            return

        options = [route["label"] for route in connected_routes]
        values = [route["value"] for route in connected_routes]

        self._route_selector.options = options
        self._route_selector.update()
        self._route_value_map = dict(zip(options, values, strict=False))

    def _is_connected(self) -> bool:
        """Check if SSH connection is available."""
        if self._parent_panel and self._selected_route is not None:
            connection = self._parent_panel.get_screen_connection(self._screen_num)
            return connection is not None and connection.is_connected()
        return False

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
            if self._parent_panel and self._selected_route is not None:
                connection = self._parent_panel.get_screen_connection(self._screen_num)
                if connection and connection.is_connected():
                    return connection.exec_command(cmd, timeout=timeout)
                return "", "No connection available"
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

        with self._system_info_container, ui.card().classes("w-full p-4 border"):
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

        with self._system_info_container, ui.card().classes("w-full p-4 border"):
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

        with self._system_info_container, ui.card().classes("w-full p-4 border"):
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

    def update_button_states(self) -> None:
        """Public method to update button states from parent."""
        self._update_button_states()

    def build(self, screen_num: int) -> None:
        """Legacy method for compatibility."""
        self.build_content(screen_num)
