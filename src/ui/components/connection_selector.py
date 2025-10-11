"""
Connection selector component for choosing host connections.
"""

from typing import List, Optional, Callable
from nicegui import ui


class ConnectionSelector:
    """Component for selecting active host connections."""

    def __init__(self, connected_routes: set, routes: list, on_connection_change: Optional[Callable] = None):
        self.connected_routes = connected_routes
        self.routes = routes
        self.on_connection_change = on_connection_change
        self.selected_connection: Optional[int] = None

    def build(self) -> ui.select:
        """Build connection selector dropdown."""
        options = self._get_connection_options()

        # Convert options to simple list for ui.select
        select_options = [opt["label"] for opt in options]

        selector = ui.select(options=select_options, value=None, label="Select Connection").classes("w-64")

        # Store the mapping for value conversion
        self._option_mapping = {opt["label"]: opt["value"] for opt in options}

        selector.on_value_change(self._on_selection_change_wrapper)
        return selector

    def _get_connection_options(self) -> List[dict]:
        """Get available connection options with tooltips."""
        options = []
        for i in self.connected_routes:
            if i < len(self.routes):
                route = self.routes[i]
                options.append({"label": route["summary"], "value": i, "tooltip": route["summary"]})
        return options

    def _on_selection_change_wrapper(self, e):
        """Handle connection selection change with label to value mapping."""
        if e.value and hasattr(self, "_option_mapping"):
            actual_value = self._option_mapping.get(e.value)
            self.selected_connection = actual_value
            if self.on_connection_change:
                self.on_connection_change(actual_value)
        else:
            self._on_selection_change(e)

    def _on_selection_change(self, e):
        """Handle connection selection change."""
        self.selected_connection = e.value
        if self.on_connection_change:
            self.on_connection_change(e.value)
