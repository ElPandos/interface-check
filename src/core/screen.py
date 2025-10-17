"""Multi-screen layout for tabs with host cards."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from nicegui import ui


@dataclass
class GridConfig:
    """Grid layout configuration."""

    screens_per_row: int = 2
    max_screens: int = 8


class ScreenBase(ABC):
    """Base screen layout functionality."""

    def __init__(self) -> None:
        self.num_screens = 1
        self.container: ui.column | None = None
        self._grid_config = GridConfig()

    def _build_content_base(self) -> None:
        """Build the base content container."""
        self.container = ui.column().classes("w-full h-full")
        with self.container:
            self._render_screens()

    def _render_screens(self) -> None:
        """Render screens dynamically in a responsive grid layout."""
        if not self.container:
            return

        self.container.clear()

        if self.num_screens == 1:
            with self.container:
                self._build_screen(1, "w-full h-full")
        elif self.num_screens == 2:
            with self.container, ui.row().classes("w-full h-full gap-2"):
                for i in range(1, 3):
                    self._build_screen(i, "flex-1 h-full")
        else:
            self._render_grid_layout()

    def _render_grid_layout(self) -> None:
        """Render screens in grid layout for 3+ screens."""
        if not self.container:
            return

        rows_needed = (self.num_screens + self._grid_config.screens_per_row - 1) // self._grid_config.screens_per_row

        with self.container, ui.column().classes("w-full h-full gap-2"):
            screen_index = 1
            for _ in range(rows_needed):
                with ui.row().classes("w-full flex-1 gap-2"):
                    screens_in_row = min(self._grid_config.screens_per_row, self.num_screens - screen_index + 1)
                    for _ in range(screens_in_row):
                        self._build_screen(screen_index, "flex-1 h-full")
                        screen_index += 1

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""


class SingleScreen(ScreenBase):
    """Single-screen layout functionality."""

    def __init__(self) -> None:
        super().__init__()
        self.num_screens = 1  # Fixed at 1 for single screen

    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build single screen content."""
        self._build_single_screen_content(classes)

    @abstractmethod
    def _build_single_screen_content(self, classes: str) -> None:
        """Build single screen content. Must be implemented by subclass."""


class MultiScreen(ScreenBase):
    """Multi-screen layout functionality."""

    def __init__(self, icon_name: str = "dashboard") -> None:
        super().__init__()
        self._icon_name = icon_name
        self._route_selector: ui.select | None = None
        self._screen_routes: dict[int, int] = {}  # screen_num -> route_index
        self._selected_routes: list[int] = []  # selected route indices
        self._host_handler = None

    def _build_control_base(self, label: str) -> None:
        """Build standard controls with route selector."""
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.icon(self._icon_name, size="lg").classes("text-blue-600")
            ui.label(label).classes("text-2xl font-bold")
            ui.space()
            self._route_selector = (
                ui.select(options=[], value=None, label="Connected Routes", multiple=True)
                .classes("w-64")
                .on_value_change(self._on_route_change)
            )
            ui.select(options=list(range(1, self._grid_config.max_screens + 1)), value=1, label="Screens").classes(
                "w-32"
            ).on_value_change(self._on_screen_change)

    def _update_route_options(self) -> None:
        """Update route selector options with connected routes."""
        if self._host_handler and self._route_selector:
            connected_routes = self._host_handler.get_connected_routes()
            print(f"DEBUG: Connected routes: {connected_routes}")  # Debug
            self._route_selector.options = connected_routes

    def set_host_handler(self, host_handler) -> None:
        """Set host handler and update route options."""
        self._host_handler = host_handler
        if self._route_selector:
            self._update_route_options()
            # Refresh route options every 2 seconds
            ui.timer(2.0, self._update_route_options, active=True)

    def _on_route_change(self, e: Any) -> None:
        """Handle route selection change."""
        if hasattr(e, "value") and e.value:
            selected_routes = e.value if isinstance(e.value, list) else [e.value]
            self._selected_routes = selected_routes
            self._update_screen_routes()

    def _on_screen_change(self, e: Any) -> None:
        """Handle screen count change."""
        if hasattr(e, "value") and 1 <= e.value <= self._grid_config.max_screens:
            self.num_screens = e.value
            self._update_screen_routes()

    def _update_screen_routes(self) -> None:
        """Update screen to route mapping and render."""
        if hasattr(self, "_selected_routes") and self._selected_routes:
            # Distribute routes across screens (cycle through routes if more screens than routes)
            self._screen_routes = {}
            for i in range(self.num_screens):
                route_idx = self._selected_routes[i % len(self._selected_routes)]
                self._screen_routes[i + 1] = route_idx
        self._render_screens()

    def get_screen_connection(self, screen_num: int):
        """Get SSH connection for a specific screen."""
        if self._host_handler and screen_num in self._screen_routes:
            route_index = self._screen_routes[screen_num]
            return self._host_handler.get_route_connection(route_index)
        return None

    def refresh_routes(self) -> None:
        """Refresh route options from host handler."""
        self._update_route_options()

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""
