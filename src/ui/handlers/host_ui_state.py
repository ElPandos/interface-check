"""Host UI state management."""

from typing import Any
from nicegui import ui


class HostUIState:
    """Manages UI state for host handler."""

    def __init__(self) -> None:
        # UI components
        self.table_container: ui.column | None = None
        self.routes_container: ui.column | None = None
        self.hosts_toggle_btn: ui.button | None = None
        self.routes_toggle_btn: ui.button | None = None
        self.add_route_btn: ui.button | None = None

        # Expansion states
        self.hosts_expanded: bool = True
        self.routes_expanded: bool = True

        # Selection states
        self.selected_host_index: int | None = None
        self.selected_route_index: int | None = None

        # Row tracking
        self.host_rows: dict[int, ui.row] = {}
        self.route_rows: dict[int, ui.row] = {}

    def clear_host_selection(self) -> None:
        """Clear host selection."""
        self.selected_host_index = None

    def clear_route_selection(self) -> None:
        """Clear route selection."""
        self.selected_route_index = None

    def toggle_hosts_expansion(self) -> None:
        """Toggle hosts table expansion."""
        self.hosts_expanded = not self.hosts_expanded
        if self.hosts_toggle_btn:
            icon = "expand_less" if self.hosts_expanded else "expand_more"
            self.hosts_toggle_btn.props(f'icon="{icon}"')

    def toggle_routes_expansion(self) -> None:
        """Toggle routes table expansion."""
        self.routes_expanded = not self.routes_expanded
        if self.routes_toggle_btn:
            icon = "expand_less" if self.routes_expanded else "expand_more"
            self.routes_toggle_btn.props(f'icon="{icon}"')

    def update_add_route_button(self, has_remote_host: bool) -> None:
        """Update add route button state."""
        if self.add_route_btn:
            if has_remote_host:
                self.add_route_btn.props(remove="disable")
                self.add_route_btn.classes(replace="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded")
            else:
                self.add_route_btn.props(add="disable")
                self.add_route_btn.classes(replace="bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")

    def reset_expansion_states(self) -> None:
        """Reset expansion states to default."""
        self.hosts_expanded = True
        self.routes_expanded = True

        if self.hosts_toggle_btn:
            self.hosts_toggle_btn.props("icon=expand_less")
        if self.routes_toggle_btn:
            self.routes_toggle_btn.props("icon=expand_less")

    def clear_containers(self) -> None:
        """Clear UI containers."""
        if self.table_container:
            self.table_container.clear()
        if self.routes_container:
            self.routes_container.clear()

        self.host_rows.clear()
        self.route_rows.clear()
