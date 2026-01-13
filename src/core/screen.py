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
        """Initialize screen base."""
        self.num_screens = 1
        self.container: ui.column | None = None
        self._grid_cfg = GridConfig()

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

        rows_needed = (self.num_screens + self._grid_cfg.screens_per_row - 1) // self._grid_cfg.screens_per_row

        with self.container, ui.column().classes("w-full h-full gap-2"):
            screen_index = 1
            for _ in range(rows_needed):
                with ui.row().classes("w-full flex-1 gap-2"):
                    screens_in_row = min(self._grid_cfg.screens_per_row, self.num_screens - screen_index + 1)
                    for _ in range(screens_in_row):
                        self._build_screen(screen_index, "flex-1 h-full")
                        screen_index += 1

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""


class SingleScreen(ScreenBase):
    """Single-screen layout functionality."""

    def __init__(self) -> None:
        """Initialize single screen."""
        super().__init__()
        self.num_screens = 1  # Fixed at 1 for single screen

    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build single screen content.

        Args:
            screen_num: Screen number
            classes: CSS classes
        """
        self._build_single_screen_content(classes)

    @abstractmethod
    def _build_single_screen_content(self, classes: str) -> None:
        """Build single screen content.

        Args:
            classes: CSS classes
        """


class MultiScreen(ScreenBase):
    """Multi-screen layout functionality."""

    def __init__(self, icon_name: str = "dashboard") -> None:
        """Initialize multi screen.

        Args:
            icon_name: Icon name for header
        """
        super().__init__()
        self._icon_name = icon_name
        self._screen_routes: dict[int, int] = {}  # screen_num -> route_index
        self._host_handler = None

    def _build_control_base(self, label: str) -> None:
        """Build standard controls.

        Args:
            label: Control label
        """
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.icon(self._icon_name, size="lg").classes("text-blue-600")
            ui.label(label).classes("text-2xl font-bold")
            ui.space()
            ui.select(options=list(range(1, self._grid_cfg.max_screens + 1)), value=1, label="Screens").classes(
                "w-32"
            ).on_value_change(self._on_screen_change)

    def get_connected_route_options(self) -> list[dict[str, Any]]:
        """Get connected route options for screen selectors.

        Returns:
            List of route options
        """
        if not self._host_handler:
            return []

        connected_routes = self._host_handler.get_connected_routes()
        return sorted(connected_routes, key=lambda x: x["value"])

    def set_host_handler(self, host_handler) -> None:
        """Set host handler.

        Args:
            host_handler: Host handler instance
        """
        self._host_handler = host_handler

    def set_screen_route(self, screen_num: int, route_index: int | None) -> None:
        """Set route for specific screen.

        Args:
            screen_num: Screen number
            route_index: Route index or None
        """
        if route_index is not None:
            self._screen_routes[screen_num] = route_index
        else:
            self._screen_routes.pop(screen_num, None)

    def _on_screen_change(self, e: Any) -> None:
        """Handle screen count change.

        Args:
            e: Event object
        """
        if hasattr(e, "value") and 1 <= e.value <= self._grid_cfg.max_screens:
            self.num_screens = e.value
            self._render_screens()
            self._update_screen_routes()

    def _update_screen_routes(self) -> None:
        """Update screen routes after screen count change."""
        # Remove routes for screens that no longer exist
        screens_to_remove = [screen for screen in self._screen_routes if screen > self.num_screens]
        for screen in screens_to_remove:
            self._screen_routes.pop(screen, None)

    def get_screen_connection(self, screen_num: int):
        """Get SSH connection for a specific screen.

        Args:
            screen_num: Screen number

        Returns:
            SSH connection or None
        """
        if self._host_handler and screen_num in self._screen_routes:
            route_index = self._screen_routes[screen_num]
            return self._host_handler.get_route_connection(route_index)
        return None

    def is_screen_connected(self, screen_num: int) -> bool:
        """Check if screen has connected route.

        Args:
            screen_num: Screen number

        Returns:
            True if connected
        """
        return screen_num in self._screen_routes

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""
