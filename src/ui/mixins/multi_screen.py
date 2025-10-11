"""Multi-screen layout mixin for tabs with host cards."""

from abc import ABC, abstractmethod

from nicegui import ui


class MultiScreenMixin(ABC):
    """Mixin providing common multi-screen layout functionality."""

    def __init__(self):
        self.num_screens = 1
        self.screen_connections = {}
        self.content_container = None

    def _build_controls_base(self, label: str) -> None:
        """Build standard controls with host selector."""
        with ui.card().classes("w-full mb-4"):
            with ui.row().classes("w-full items-center gap-4"):
                ui.label(label).classes("text-lg font-bold")
                ui.space()
                ui.select([1, 2, 3, 4], value=1, label="Hosts").classes("w-32").on_value_change(self._on_screen_change)

    def _build_content_base(self) -> None:
        """Build standard content container."""
        self.content_container = ui.column().classes("w-full h-full")
        with self.content_container:
            self._render_screens()

    def _render_screens(self):
        """Render screens in responsive grid layout."""
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

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    def _on_screen_change(self, e):
        """Handle screen count change."""
        self.num_screens = e.value
        self._render_screens()
        self._update_icon_status()

    def _on_connection_change(self, connection_id, screen_num):
        """Handle connection selection change."""
        if not hasattr(self, "screen_connections"):
            self.screen_connections = {}
        self.screen_connections[screen_num] = connection_id
        self._update_icon_status()

    def _update_icon_status(self):
        """Update tab icon color based on connection status."""
