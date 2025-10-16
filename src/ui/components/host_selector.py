"""Host selector component for tabs with multiscreen support."""

from typing import Callable

from nicegui import ui

from src.ui.handlers.host import HostManager


class HostSelector:
    """Reusable host selector component."""

    def __init__(self, host_manager: HostManager, on_change: Callable[[int | None], None] | None = None) -> None:
        self._host_manager = host_manager
        self._on_change = on_change
        self._selector = None
        self._status_icon = None

    def build(self) -> ui.row:
        """Build host selector with connection status."""
        with ui.row().classes("items-center gap-2") as container:
            ui.label("Host:").classes("text-sm font-medium")

            self._selector = self._host_manager.create_host_selector(self._on_change)

            self._status_icon = ui.icon("circle", size="sm").classes("text-gray-400")
            self._update_status_icon()

            # Register for connection updates
            self._host_manager.register_connection_callback(self._on_connection_change)

        return container

    def _on_connection_change(self, connection) -> None:
        """Handle connection status changes."""
        self._update_status_icon()

    def _update_status_icon(self) -> None:
        """Update connection status icon."""
        if self._status_icon:
            if self._host_manager.is_connected:
                self._status_icon.props("name=check_circle color=positive")
                self._status_icon.tooltip("Connected")
            else:
                self._status_icon.props("name=circle color=grey")
                self._status_icon.tooltip("Not connected")
