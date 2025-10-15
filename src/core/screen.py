"""Multi-screen layout for tabs with host cards."""

from abc import ABC, abstractmethod
import math

from nicegui import ui


class ScreenBase(ABC):
    """Base screen layout functionality."""

    def __init__(self):
        self.num_screens = 1
        self.container = None
        self.screen_connections = {}

    def _build_content_base(self) -> None:
        self.container = ui.column().classes("w-full h-full")
        with self.container:
            self._render_screens()

    def _render_screens(self):
        """Render screens dynamically in a responsive grid layout."""
        self.container.clear()

        # Special handling for 1 or 2 screens
        if self.num_screens == 1:
            with self.container:
                self._build_screen(1, "w-full h-full")
            return

        if self.num_screens == 2:
            with self.container, ui.row().classes("w-full h-full gap-2"):
                for i in range(1, 3):
                    self._build_screen(i, "flex-1 h-full")
            return

        # General layout for 3+ screens
        screens_per_row = 2
        total_rows = math.ceil(self.num_screens / screens_per_row)

        with self.container, ui.column().classes("w-full h-full gap-2"):
            screen_index = 1
            for _ in range(total_rows):
                with ui.row().classes("w-full flex-1 gap-2"):
                    for _ in range(screens_per_row):
                        if screen_index <= self.num_screens:
                            self._build_screen(screen_index, "flex-1 h-full")
                            screen_index += 1

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""


class SingleScreen(ScreenBase):
    """Common single-screen layout functionality."""

    def __init__(self):
        ScreenBase.__init__(self)

    @abstractmethod
    def _build_screen(self, classes: str) -> None:
        """Build individual screen content. Must be implemented by subclass."""

    def _on_screen_change(self, e):
        """Handle screen count change."""
        self._render_screens()
        # This can redraw state of buttons ect.


class MultiScreen(ScreenBase):
    """Common multi-screen layout functionality."""

    __MAX_SCREENS = 8
    __SELECTOR_LABEL = "Hosts"

    def __init__(self):
        ScreenBase.__init__(self)

    def _build_control_base(self, label: str) -> None:
        """Build standard controls with host selector."""
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.icon(self._ICON_NAME, size="lg").classes("text-blue-600")
            ui.label(label).classes("text-lg font-bold")
            ui.space()
            ui.select(options=list(range(1, self.__MAX_SCREENS + 1)), value=1, label=self.__SELECTOR_LABEL).classes(
                "w-32"
            ).on_value_change(self._on_screen_change)

    @abstractmethod
    def _build_screen(self, screen_num: int, classes: str) -> None:
        """Build individual screena content. Must be implemented by subclass."""

    def _on_screen_change(self, e):
        """Handle screen count change."""
        self.num_screens = e.value
        self._render_screens()
