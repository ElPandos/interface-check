"""SSH Host Manager - Optimized Implementation"""

import logging
from typing import Any

from nicegui import ui

from src.core.config import Configure
from src.core.json import Json
from src.core.screen import SingleScreen
from src.core.validation import HostValidator
from src.models.config import Config, Host, Networks, Route
from src.platform.enums.log import LogName
from src.ui.handlers.host import HostHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.ui.themes.style import apply_global_theme

logger = logging.getLogger(LogName.MAIN.value)

NAME = "hosts"
LABEL = "Host"
MAX_INPUT_LENGTH = 255

# Common CSS classes
BUTTON_STYLES = {
    "primary": "bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded",
    "secondary": "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded",
    "danger": "bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded",
    "warning": "bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded",
    "success": "bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded",
    "disabled": "bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded",
}

CARD_STYLES = "w-full bg-white border border-gray-200 shadow-sm p-4"
HEADER_STYLES = "font-bold text-white bg-gradient-to-r w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"


class HostTab(BaseTab):
    ICON_NAME = "home"

    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()


class HostPanel(BasePanel, SingleScreen):
    def __init__(self, cfg: Config, host_handler: HostHandler, build: bool = False):
        BasePanel.__init__(self, NAME, LABEL, HostTab.ICON_NAME)
        SingleScreen.__init__(self)
        self._cfg = cfg
        self._host_handler = host_handler
        if build:
            self.build()

    def build(self) -> None:
        with ui.tab_panel(self.name).classes("w-full h-screen"):
            self._build_content_base()

    def _build_single_screen_content(self, classes: str) -> None:
        self._host_content = HostContent(self._host_handler)
        self._host_content.build()


class HostContent:
    """Optimized SSH Host Manager."""

    def __init__(self, host_handler: HostHandler) -> None:
        self.config = HostConfigManager()
        self._host_handler = host_handler

        # UI state
        self.hosts_expanded = True
        self.routes_expanded = True
        self.selected_host_index: int | None = None
        self.selected_route_index: int | None = None

        # UI components
        self.table_container: ui.column | None = None
        self.routes_container: ui.column | None = None
        self.add_route_btn: ui.button | None = None
        self._undo_btn: ui.button | None = None

        # Cache
        self._remote_hosts_cache: list[dict[str, Any]] | None = None
        self._jump_hosts_cache: list[dict[str, Any]] | None = None
        self._cache_dirty = True

        # Undo state
        self._last_deletion: dict[str, Any] | None = None

        self.config.load()

    def build(self) -> None:
        """Build UI."""
        try:
            apply_global_theme()
            self._build_layout()
            self._refresh_tables()
        except Exception:
            logger.exception("Failed to initialize UI")
            ui.notify("Failed to initialize interface", color="negative")

    def _build_layout(self) -> None:
        """Build main layout."""
        with ui.card().classes("w-full p-4 border"):
            self._build_header()
            self._build_hosts_section()
            self._build_routes_section()

    def _build_header(self) -> None:
        """Build header with action buttons."""
        with ui.row().classes("w-full justify-center items-center gap-3 mb-6"):
            ui.icon("home", size="lg").classes("text-blue-600")
            ui.label("SSH Host Manager").classes("text-2xl font-bold text-gray-800")
            ui.space()

            # Action buttons
            for icon, action, tooltip in [
                ("save", self._save_cfg, "Save configuration"),
                ("download", self._open_import_dialog, "Import configuration"),
                ("upload", self._export_cfg, "Export configuration"),
            ]:
                ui.button(icon=icon, on_click=action).classes(BUTTON_STYLES["secondary"]).tooltip(tooltip)

            self._undo_btn = (
                ui.button(icon="undo", on_click=self._show_undo_dialog)
                .props("disable")
                .classes(BUTTON_STYLES["disabled"])
                .tooltip("Undo last deletion")
            )

    def _build_hosts_section(self) -> None:
        """Build hosts section."""
        with ui.card().classes(CARD_STYLES):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                ui.button(icon="expand_less", on_click=self._toggle_hosts).props("flat round").classes("text-gray-600")
                ui.icon("computer", size="lg").classes("text-blue-600")
                ui.label("Hosts").classes("text-2xl font-semibold text-gray-800")
                ui.space()
                ui.button(icon="desktop_windows", text="Add Host", on_click=self._open_add_dialog).classes(
                    BUTTON_STYLES["secondary"]
                )
            self.table_container = ui.column().classes("w-full")

    def _build_routes_section(self) -> None:
        """Build routes section."""
        with ui.card().classes(CARD_STYLES):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                ui.button(icon="expand_less", on_click=self._toggle_routes).props("flat round").classes("text-gray-600")
                ui.icon("route", size="lg").classes("text-green-600")
                ui.label("Routes").classes("text-2xl font-semibold text-gray-800")
                ui.space()
                self.add_route_btn = (
                    ui.button(icon="route", text="Add Route", on_click=self._add_route)
                    .props("disable")
                    .classes(BUTTON_STYLES["disabled"])
                )
            self.routes_container = ui.column().classes("w-full")

    def _invalidate_cache(self) -> None:
        """Invalidate host cache."""
        self._cache_dirty = True
        self._remote_hosts_cache = self._jump_hosts_cache = None

    def _get_remote_hosts(self) -> list[dict[str, Any]]:
        """Get cached remote hosts."""
        if self._cache_dirty or self._remote_hosts_cache is None:
            self._remote_hosts_cache = [h for h in self.config.hosts if h.get("remote", False)]
        return self._remote_hosts_cache

    def _get_jump_hosts(self) -> list[dict[str, Any]]:
        """Get cached jump hosts."""
        if self._cache_dirty or self._jump_hosts_cache is None:
            self._jump_hosts_cache = [h for h in self.config.hosts if h.get("jump", False)]
        return self._jump_hosts_cache

    def _save_cfg(self) -> None:
        """Save configuration."""
        try:
            self.config.save()
            ui.notify("Configuration saved", color="positive")
        except Exception:
            logger.exception("Error saving config")
            ui.notify("Failed to save configuration", color="negative")

    def _open_add_dialog(self) -> None:
        """Open add host dialog."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Add new host").classes("text-xl font-bold mb-6 text-center text-gray-800")

            # Input fields
            info_input = ui.input("Info", placeholder="Description or notes").classes("w-full mb-3").props("outlined")
            ip_input = ui.input("IP address", placeholder="192.168.1.100").classes("w-full mb-3").props("outlined")
            user_input = ui.input("Username", placeholder="admin").classes("w-full mb-3").props("outlined")
            pass_input = (
                ui.input("Password", password=True, placeholder="••••••••").classes("w-full mb-6").props("outlined")
            )

            # Action buttons
            with ui.row().classes("w-full gap-2"):
                ui.button(
                    "Add host",
                    on_click=lambda: self._add_host(
                        HostValidator.sanitize_input(ip_input.value or ""),
                        HostValidator.sanitize_input(user_input.value or ""),
                        HostValidator.sanitize_input(pass_input.value or ""),
                        HostValidator.sanitize_input(info_input.value or ""),
                        dialog,
                    ),
                ).classes(BUTTON_STYLES["primary"])
                ui.button("Cancel", on_click=dialog.close).classes(BUTTON_STYLES["secondary"])

        dialog.open()

    def _add_host(self, ip: str, username: str, password: str, info: str, dialog: ui.dialog) -> None:
        """Add new host."""
        try:
            error_msg = HostValidator.validate_host_data(ip, username, password, self.config.hosts)
            if error_msg:
                ui.notify(error_msg, color="negative")
                return

            self.config.add_host(
                {
                    "ip": ip,
                    "username": username,
                    "password": password,
                    "info": info,
                    "remote": False,
                    "jump": False,
                    "jump_order": None,
                }
            )
            self.config.save()
            dialog.close()
            ui.notify(f"Successfully added host {ip}", color="positive")
            self._refresh_tables()
        except Exception:
            logger.exception("Error adding host")
            ui.notify("Failed to add host", color="negative")

    def _toggle_hosts(self) -> None:
        """Toggle hosts table visibility."""
        self.hosts_expanded = not self.hosts_expanded
        self._refresh_hosts_table()

    def _toggle_routes(self) -> None:
        """Toggle routes table visibility."""
        self.routes_expanded = not self.routes_expanded
        self._refresh_routes_table()

    def _add_route(self) -> None:
        """Add new route."""
        try:
            remote_hosts = self._get_remote_hosts()
            if not remote_hosts:
                ui.notify("Please select a target host first", color="negative")
                return

            jump_hosts = self._get_jump_hosts()
            remote_host = remote_hosts[0]

            # Build summary
            if jump_hosts:
                sorted_jumps = sorted(jump_hosts, key=lambda h: h.get("jump_order", 0))
                summary = f"{' ⟶ '.join(h['ip'] for h in sorted_jumps)} ⟶ {remote_host['ip']} (Target)"
            else:
                summary = f"Direct ⟶ {remote_host['ip']} (Target)"

            # Check duplicates
            existing_summaries = {self._get_route_summary(r) for r in self.config.routes}
            if summary in existing_summaries:
                ui.notify("Route already exists", color="negative")
                return

            # Create route
            route_data = {
                "summary": summary,
                "target": {k: remote_host[k] for k in ("ip", "username", "password", "info")},
                "jumps": [{k: jump[k] for k in ("ip", "username", "password", "info")} for jump in jump_hosts],
            }

            self.config.add_route(route_data)
            self.config.save()

            # Reset selections
            for host in self.config.hosts:
                host.update({"remote": False, "jump": False, "jump_order": None})
            self.config.remote_index = None
            self._invalidate_cache()

            ui.notify(f"Route added: {summary}", color="positive")
            self._refresh_tables()
        except Exception:
            logger.exception("Error adding route")

    def _connect_route(self, index: int) -> None:
        """Connect to route."""
        try:
            if not self.config.routes:
                ui.notify("No routes available", color="negative")
                return

            if not (0 <= index < len(self.config.routes)):
                ui.notify(f"Invalid route index: {index}", color="negative")
                logger.error("Invalid route index: %s (max: %s)", index + 1, len(self.config.routes))
                return

            if self._host_handler.connect_to_route(index):
                self._refresh_routes_table()
        except Exception:
            logger.exception("Error connecting to route")

    def _disconnect_route(self, index: int) -> None:
        """Disconnect from route."""
        if 0 <= index < len(self.config.routes):
            self._host_handler.disconnect_from_route(index)
            self._refresh_routes_table()
        else:
            logger.error("Invalid route index for disconnect: %s", index + 1)

    def _delete_route(self, index: int) -> None:
        """Delete route."""
        try:
            if not (0 <= index < len(self.config.routes)):
                logger.error("Invalid route index for delete: %s", index + 1)
                return

            if self._host_handler.is_route_connected(index):
                self._host_handler.disconnect_from_route(index)

            deleted_route = self.config.routes[index]
            if self.config.delete_route(index):
                self._last_deletion = {
                    "type": "route_only",
                    "host": None,
                    "routes": [(index, deleted_route)],
                }
                self._update_undo_button()
                ui.notify("Route removed", color="warning")
                self.config.save()
                self._refresh_routes_table()
        except Exception:
            logger.exception("Error deleting route")

    def _refresh_tables(self) -> None:
        """Refresh both tables."""
        self._refresh_hosts_table()
        self._refresh_routes_table()

    def _refresh_hosts_table(self) -> None:
        """Refresh hosts table."""
        if not self.table_container:
            return

        try:
            self.table_container.clear()
            if not self.hosts_expanded:
                return

            with self.table_container:
                # Header
                with ui.row().classes(f"{HEADER_STYLES} from-blue-500 to-gray-500"):
                    for label, width in [
                        ("Move", "w-16"),
                        ("#", "w-6"),
                        ("Info", "w-32"),
                        ("IP Address", "w-40"),
                        ("Username", "w-36"),
                        ("Password", "w-36"),
                        ("Target", "w-28"),
                        ("Jump", "w-24"),
                        ("Order", "w-16"),
                        ("Actions", "w-20"),
                    ]:
                        ui.label(label).classes(f"{width} text-center text-white font-bold")

                # Data rows
                for i, host in enumerate(self.config.hosts):
                    self._render_host_row(i, host)

            self._update_add_route_button()
        except Exception:
            logger.exception("Error refreshing hosts table")

    def _render_host_row(self, index: int, host: dict[str, Any]) -> None:
        """Render host row."""
        is_remote = host.get("remote", False)
        is_jump = host.get("jump", False)
        is_selected = self.selected_host_index == index

        # Row styling
        if is_selected:
            row_bg = "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"
        elif is_remote:
            row_bg = "bg-gradient-to-r from-white to-blue-500 border-blue-400"
        elif is_jump:
            row_bg = "bg-gradient-to-r from-white to-blue-200 border-blue-300"
        else:
            row_bg = f"bg-gradient-to-r from-white to-{'gray-50' if index % 2 else 'white'} border-gray-200"

        with ui.row().classes(
            f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-gray-100"
        ):
            # Controls
            ui.button(icon="drag_indicator", on_click=lambda i=index: self._select_host_for_move(i)).props(
                "flat"
            ).classes("text-gray-400 w-16")
            ui.label(str(index + 1)).classes("w-6 text-center text-gray-600")
            ui.label(host.get("info", "")).classes("w-32 text-center text-gray-800 truncate").tooltip(
                host.get("info", "")
            )
            ui.label(host["ip"]).classes("w-40 text-center text-gray-800")
            ui.label(host["username"]).classes("w-36 text-center text-gray-800")
            ui.label("••••••").classes("w-36 text-center text-gray-500").tooltip(host["password"])

            # Checkboxes
            with ui.column().classes("w-28 items-center"):
                cb_remote = ui.checkbox(value=is_remote)
                cb_remote.on_value_change(lambda e, i=index: self._on_remote_toggle(checked=e.value, index=i))
                if getattr(self.config, "remote_index", None) is not None and not is_remote:
                    cb_remote.disable()

            with ui.column().classes("w-24 items-center"):
                cb_jump = ui.checkbox(value=is_jump)
                cb_jump.on_value_change(lambda e, i=index: self._on_jump_toggle(checked=e.value, index=i))
                if is_remote or getattr(self.config, "remote_index", None) is None:
                    cb_jump.disable()

            # Order select
            with ui.column().classes("w-16 items-center"):
                order_value = str(host.get("jump_order", "")) if host.get("jump_order") else None
                order_select = ui.select(self._get_available_orders(host), value=order_value).props("outlined dense")
                order_select.on_value_change(lambda e, i=index: self._on_jump_order_change(e.value, i))
                if not is_jump or is_remote:
                    order_select.disable()

            # Delete button
            with ui.column().classes("w-20 items-center"):
                ui.button(icon="delete", on_click=lambda i=index: self._delete_host(i)).props("unelevated").classes(
                    "bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded"
                )

    def _refresh_routes_table(self) -> None:
        """Refresh routes table."""
        if not self.routes_container:
            return

        try:
            self.routes_container.clear()
            if not self.routes_expanded:
                return

            with self.routes_container:
                # Header
                with ui.row().classes(f"{HEADER_STYLES} from-green-600 to-gray-500"):
                    for label, width in [
                        ("Move", "w-16"),
                        ("#", "w-6"),
                        ("Route Summary", "flex-1"),
                        ("Actions", "w-40"),
                    ]:
                        ui.label(label).classes(f"{width} text-center text-white font-bold")

                # Data rows
                if not self.config.routes:
                    ui.label("No routes defined yet.").classes(
                        "text-gray-500 italic text-center py-4 bg-white border-b border-gray-200"
                    )
                else:
                    for i, route_data in enumerate(self.config.routes):
                        self._render_route_row(i, route_data)
        except Exception:
            logger.exception("Error refreshing routes table")

    def _render_route_row(self, index: int, route_data: Any) -> None:
        """Render route row."""
        is_selected = self.selected_route_index == index
        row_bg = (
            "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"
            if is_selected
            else f"bg-{'green-50' if index % 2 else 'white'} border-{'green' if index % 2 else 'gray'}-200"
        )

        with ui.row().classes(
            f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-green-100"
        ):
            with ui.column().classes("w-16 items-center"):
                ui.button(icon="drag_indicator", on_click=lambda i=index: self._select_route_for_move(i)).props(
                    "flat"
                ).classes("text-gray-400")
            ui.label(str(index + 1)).classes("w-6 text-center text-gray-600")
            ui.label(self._get_route_summary(route_data)).classes("flex-1 truncate text-gray-800 text-center")

            with ui.row().classes("gap-2 w-40 justify-center"):
                # Connect/Disconnect button
                is_connected = self._host_handler.is_route_connected(index)
                if is_connected:
                    ui.button(icon="power_off", on_click=lambda idx=index: self._disconnect_route(idx)).props(
                        "unelevated color=red"
                    ).classes("text-white w-16 h-8 rounded").tooltip("Disconnect from route")
                else:
                    ui.button(icon="power", on_click=lambda idx=index: self._connect_route(idx)).props(
                        "unelevated color=green"
                    ).classes("text-white w-16 h-8 rounded").tooltip("Connect to route")

                # Delete button
                ui.button(icon="delete", on_click=lambda idx=index: self._delete_route(idx)).props(
                    "unelevated"
                ).classes("bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded")

    def _get_route_summary(self, route_data: Any) -> str:
        """Get route summary safely."""
        return (
            route_data.get("summary", str(route_data))
            if isinstance(route_data, dict)
            else getattr(route_data, "summary", str(route_data))
        )

    def _update_add_route_button(self) -> None:
        """Update add route button state."""
        if not self.add_route_btn:
            return

        has_remote = bool(self._get_remote_hosts())
        if has_remote:
            self.add_route_btn.props(remove="disable").classes(remove=BUTTON_STYLES["disabled"]).classes(
                add=BUTTON_STYLES["primary"]
            )
        else:
            self.add_route_btn.props(add="disable").classes(add=BUTTON_STYLES["disabled"]).classes(
                remove=BUTTON_STYLES["primary"]
            )

    def _on_remote_toggle(self, *, checked: bool, index: int) -> None:
        """Handle remote host toggle."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            if checked:
                for host in self.config.hosts:
                    host["remote"] = False
                self.config.hosts[index]["remote"] = True
                self.config.remote_index = index
            else:
                self.config.remote_index = None
                self.config.hosts[index]["remote"] = False

            self._invalidate_cache()
            self.config.save()
            self._refresh_hosts_table()
        except Exception:
            logger.exception("Error toggling remote host")

    def _on_jump_toggle(self, *, checked: bool, index: int) -> None:
        """Handle jump host toggle."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            host = self.config.hosts[index]
            host["jump"] = checked

            if checked:
                used_orders = {h.get("jump_order") for h in self.config.hosts if h.get("jump_order") and h != host}
                host["jump_order"] = next(
                    (order for order in range(1, len(self.config.hosts) + 1) if order not in used_orders),
                    1,
                )
            else:
                host["jump_order"] = None

            self._invalidate_cache()
            self.config.save()
            self._refresh_hosts_table()
        except Exception:
            logger.exception("Error toggling jump host")

    def _on_jump_order_change(self, value: str, index: int) -> None:
        """Handle jump order change."""
        try:
            if 0 <= index < len(self.config.hosts):
                order = None
                if value and value.strip():
                    try:
                        order = int(value)
                        if order < 1:
                            order = None
                    except ValueError:
                        order = None
                self.config.hosts[index]["jump_order"] = order
                self.config.save()
        except Exception:
            logger.exception("Error updating jump order")

    def _get_available_orders(self, current_host: dict[str, Any]) -> list[str]:
        """Get available jump orders."""
        target_count = sum(1 for h in self.config.hosts if h.get("remote", False))
        max_order = len(self.config.hosts) - target_count
        used_orders = {h.get("jump_order") for h in self.config.hosts if h.get("jump_order") and h != current_host}
        return [str(j) for j in range(1, max_order + 1) if j not in used_orders]

    def _select_host_for_move(self, index: int) -> None:
        """Select host for moving."""
        if self.selected_host_index == index:
            self.selected_host_index = None
        elif self.selected_host_index is not None:
            self._move_host(self.selected_host_index, index)
            self.selected_host_index = None
        else:
            self.selected_host_index = index
        self._refresh_hosts_table()

    def _select_route_for_move(self, index: int) -> None:
        """Select route for moving."""
        if self.selected_route_index == index:
            self.selected_route_index = None
        elif self.selected_route_index is not None:
            self._move_route(self.selected_route_index, index)
            self.selected_route_index = None
        else:
            self.selected_route_index = index
        self._refresh_routes_table()

    def _move_host(self, from_index: int, to_index: int) -> None:
        """Move host."""
        if self.config.move_host(from_index, to_index):
            self.config.save()
            ui.notify(f"Moved host from position {from_index + 1} to {to_index + 1}", color="info")

    def _move_route(self, from_index: int, to_index: int) -> None:
        """Move route."""
        if self.config.move_route(from_index, to_index):
            self.config.save()
            ui.notify(f"Moved route from position {from_index + 1} to {to_index + 1}", color="info")

    def _delete_host(self, index: int) -> None:
        """Delete host with route checking."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            host_to_delete = self.config.hosts[index]
            host_ip = host_to_delete["ip"]

            # Find affected routes
            affected_routes = [
                (i, self._get_route_summary(route))
                for i, route in enumerate(self.config.routes)
                if host_ip in self._get_route_summary(route)
            ]

            if affected_routes:
                self._show_delete_confirmation(index, host_ip, affected_routes)
            else:
                self._perform_host_deletion(index)
        except Exception:
            logger.exception("Error deleting host")

    def _show_delete_confirmation(self, host_index: int, host_ip: str, affected_routes: list[tuple[int, str]]) -> None:
        """Show delete confirmation dialog."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label(f"Delete host {host_ip}?").classes("text-xl font-bold mb-4 text-center text-gray-800")
            ui.label(f"This host is used in {len(affected_routes)} route(s):").classes("text-gray-700 mb-2")

            with ui.column().classes("w-full mb-4 max-h-32 overflow-y-auto"):
                for _, summary in affected_routes:
                    ui.label(f"• {summary}").classes("text-sm text-gray-600")

            ui.label("Do you want to remove the affected routes too?").classes("text-gray-700 mb-4")

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    "Remove All",
                    on_click=lambda: self._delete_host_and_routes(host_index, affected_routes, dialog),
                ).classes(BUTTON_STYLES["danger"])
                ui.button("Host Only", on_click=lambda: self._perform_host_deletion(host_index, dialog)).classes(
                    BUTTON_STYLES["warning"]
                )
                ui.button("Cancel", on_click=dialog.close).classes(BUTTON_STYLES["secondary"])

        dialog.open()

    def _delete_host_and_routes(
        self, host_index: int, affected_routes: list[tuple[int, str]], dialog: ui.dialog
    ) -> None:
        """Delete host and affected routes."""
        try:
            deleted_routes = []
            route_indices = sorted([i for i, _ in affected_routes], reverse=True)

            for route_index in route_indices:
                if 0 <= route_index < len(self.config.routes):
                    deleted_routes.append((route_index, self.config.routes[route_index]))
                    self.config.delete_route(route_index)

            deleted_host = self.config.delete_host(host_index)

            if deleted_host:
                self._last_deletion = {
                    "type": "host_and_routes",
                    "host": {"index": host_index, "data": deleted_host},
                    "routes": deleted_routes,
                }
                self._update_undo_button()

            dialog.close()

            if deleted_host:
                ui.notify(
                    f"Deleted host {deleted_host['ip']} and {len(affected_routes)} route(s)",
                    color="warning",
                )
                self.config.save()
                self._refresh_tables()
        except Exception:
            logger.exception("Error deleting host and routes")

    def _perform_host_deletion(self, host_index: int, dialog: ui.dialog | None = None) -> None:
        """Perform host deletion."""
        try:
            deleted_host = self.config.delete_host(host_index)

            if deleted_host:
                self._last_deletion = {
                    "type": "host_only",
                    "host": {"index": host_index, "data": deleted_host},
                    "routes": [],
                }
                self._update_undo_button()

            if dialog:
                dialog.close()

            if deleted_host:
                ui.notify(f"Deleted host {deleted_host['ip']}", color="warning")
                self.config.save()
                self._refresh_hosts_table()
        except Exception:
            logger.exception("Error deleting host")

    def _update_undo_button(self) -> None:
        """Update undo button state."""
        if not self._undo_btn:
            return

        if self._last_deletion:
            self._undo_btn.props(remove="disable").classes(remove=BUTTON_STYLES["disabled"]).classes(
                add=BUTTON_STYLES["primary"]
            )
        else:
            self._undo_btn.props(add="disable").classes(add=BUTTON_STYLES["disabled"]).classes(
                remove=BUTTON_STYLES["primary"]
            )

    def _show_undo_dialog(self) -> None:
        """Show undo dialog."""
        if not self._last_deletion:
            return

        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Undo Last Deletion").classes("text-xl font-bold mb-4 text-center text-gray-800")

            host_data = self._last_deletion["host"]
            routes_data = self._last_deletion["routes"]

            ui.label("This will restore:").classes("text-gray-700 mb-2")

            with ui.column().classes("w-full mb-4"):
                if host_data:
                    ui.label(f"• Host: {host_data['data']['ip']}").classes("text-sm text-gray-600")
                if routes_data:
                    ui.label(f"• {len(routes_data)} route(s)").classes("text-sm text-gray-600")

            with ui.row().classes("w-full gap-2"):
                ui.button("Restore", on_click=lambda: self._perform_undo(dialog)).classes(BUTTON_STYLES["success"])
                ui.button("Cancel", on_click=dialog.close).classes(BUTTON_STYLES["secondary"])

        dialog.open()

    def _perform_undo(self, dialog: ui.dialog) -> None:
        """Perform undo operation."""
        try:
            if not self._last_deletion:
                return

            host_data = self._last_deletion["host"]
            routes_data = self._last_deletion["routes"]

            if host_data:
                host_index = min(host_data["index"], len(self.config.hosts))
                self.config.hosts.insert(host_index, host_data["data"])

            for route_index, route_data in routes_data:
                restore_index = min(route_index, len(self.config.routes))
                self.config.routes.insert(restore_index, route_data)

            self._last_deletion = None
            self._update_undo_button()
            dialog.close()

            self.config.save()
            self._refresh_tables()

            restored_items = []
            if host_data:
                restored_items.append(f"host {host_data['data']['ip']}")
            if routes_data:
                restored_items.append(f"{len(routes_data)} route(s)")

            ui.notify(f"Restored {' and '.join(restored_items)}", color="positive")
        except Exception:
            logger.exception("Error performing undo")

    def _export_cfg(self) -> None:
        """Export configuration."""
        try:
            hosts = [
                Host(
                    ip=h["ip"],
                    username=h["username"],
                    password=h["password"],
                    info=h.get("info", ""),
                )
                for h in self.config.hosts
            ]
            routes = []

            for route in self.config.routes:
                if isinstance(route, dict):
                    target_host = route.get("target", {})
                    jump_hosts = route.get("jumps", [])

                    target = Host(
                        ip=target_host.get("ip", ""),
                        username=target_host.get("username", ""),
                        password=target_host.get("password", ""),
                        info=target_host.get("info", ""),
                    )
                    jumps = [
                        Host(
                            ip=jump.get("ip", ""),
                            username=jump.get("username", ""),
                            password=jump.get("password", ""),
                            info=jump.get("info", ""),
                        )
                        for jump in jump_hosts
                    ]
                    routes.append(Route(summary=route.get("summary", ""), target=target, jumps=jumps))
                else:
                    routes.append(route)

            app_cfg = Config(networks=Networks(hosts=hosts, routes=routes))
            config_json = Json.dump_to_string(app_cfg.model_dump())
            ui.download(config_json.encode(), "ssh_cfg.json")
            ui.notify("Configuration exported successfully", color="positive")
        except Exception:
            logger.exception("Error exporting config")
            ui.notify("Failed to export configuration", color="negative")

    def _open_import_dialog(self) -> None:
        """Open import dialog."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Import configuration").classes("text-xl font-bold mb-6 text-center text-gray-800")

            ui.upload(on_upload=lambda e: self._handle_file_upload(e, dialog), auto_upload=True).props(
                "accept=.json"
            ).classes("w-full mb-4")
            ui.label("OR").classes("text-center text-gray-500 font-bold my-2")

            config_input = ui.textarea(placeholder="Paste JSON here...").classes("w-full h-32 mb-4")

            with ui.row().classes("w-full gap-2"):
                ui.button("Import", on_click=lambda: self._import_cfg(config_input.value, dialog)).classes(
                    BUTTON_STYLES["primary"]
                )
                ui.button("Cancel", on_click=dialog.close).classes(BUTTON_STYLES["secondary"])

        dialog.open()

    def _import_cfg(self, config_text: str, dialog: ui.dialog) -> None:
        """Import configuration."""
        try:
            if not config_text or not config_text.strip():
                ui.notify("Please provide configuration JSON", color="negative")
                return

            config = Json.parse_string(config_text)
            if not isinstance(config, dict):
                ui.notify("Invalid configuration format", color="negative")
                return

            # Handle both formats
            if "networks" in config:
                hosts = config["networks"].get("hosts", [])
                routes = config["networks"].get("routes", [])
            else:
                hosts = config.get("hosts", [])
                routes = config.get("routes", [])

            if not hosts:
                ui.notify("No hosts found in configuration", color="negative")
                return

            # Always show confirmation dialog
            self._show_import_confirmation(hosts, routes, dialog)
        except Exception:
            logger.exception("Error importing config")
            ui.notify("Import failed", color="negative")

    def _show_import_confirmation(self, hosts: list, routes: list, parent_dialog: ui.dialog) -> None:
        """Show import confirmation dialog."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Import Configuration").classes("text-xl font-bold mb-4 text-center text-gray-800")
            ui.label(f"Found {len(hosts)} hosts and {len(routes)} routes to import.").classes("text-gray-700 mb-4")
            ui.label("Choose import method:").classes("text-gray-700 mb-4")

            with ui.row().classes("w-full gap-2 mb-2"):
                ui.button(
                    "Overwrite All",
                    on_click=lambda: self._perform_import(
                        hosts, routes, parent_dialog, overwrite=True, confirm_dialog=dialog
                    ),
                ).classes(BUTTON_STYLES["danger"])
                ui.button(
                    "Add Missing Only",
                    on_click=lambda: self._perform_import(
                        hosts, routes, parent_dialog, overwrite=False, confirm_dialog=dialog
                    ),
                ).classes(BUTTON_STYLES["primary"])
            ui.button("Cancel", on_click=dialog.close).classes(f"{BUTTON_STYLES['secondary']} w-full")

        dialog.open()

    def _perform_import(
        self,
        hosts: list,
        routes: list,
        dialog: ui.dialog,
        overwrite: bool,
        confirm_dialog: ui.dialog | None = None,
    ) -> None:
        """Perform the actual import."""
        try:
            if overwrite:
                # Clear existing data
                self.config.hosts.clear()
                self.config.routes.clear()
                new_hosts = hosts
                new_routes = routes
            else:
                # Import new items only
                existing_ips = {h["ip"] for h in self.config.hosts}
                new_hosts = [host for host in hosts if host.get("ip") not in existing_ips]

                existing_summaries = {self._get_route_summary(r) for r in self.config.routes}
                new_routes = [
                    route
                    for route in (routes if isinstance(routes, list) else [])
                    if self._get_route_summary(route) not in existing_summaries
                ]

            self.config.hosts.extend(new_hosts)
            self.config.routes.extend(new_routes)

            # Reset selections and invalidate cache
            for host in self.config.hosts:
                host.update({"remote": False, "jump": False, "jump_order": None})
                host.setdefault("info", "")
            self.config.remote_index = None
            self._invalidate_cache()

            # Save and refresh
            self.config.save()
            if confirm_dialog:
                confirm_dialog.close()
            dialog.close()
            self._refresh_tables()

            action = "Replaced" if overwrite else "Imported"
            ui.notify(f"{action} {len(new_hosts)} hosts and {len(new_routes)} routes", color="positive")
        except Exception:
            logger.exception("Error performing import")
            ui.notify("Import failed", color="negative")

    def _handle_file_upload(self, e, dialog: ui.dialog) -> None:
        """Handle file upload."""
        try:
            if e.content:
                config_text = e.content.read().decode("utf-8")
                # Don't close the dialog yet, let _import_cfg handle it
                self._import_cfg(config_text, dialog)
        except Exception:
            logger.exception("Error handling file upload")
            ui.notify("Failed to read uploaded file", color="negative")


class HostConfigManager:
    """Optimized configuration manager."""

    def __init__(self) -> None:
        self.hosts: list[dict[str, Any]] = []
        self.routes: list[dict[str, Any]] = []
        self.remote_index: int | None = None

    def load(self) -> None:
        """Load configuration."""
        try:
            config = Configure().load()
            self.hosts = [
                {
                    "ip": host.ip,
                    "username": host.username,
                    "password": host.password.get_secret_value(),
                    "info": host.info,
                }
                for host in config.networks.hosts
            ]

            self.routes = []
            for route in config.networks.routes:
                if isinstance(route, dict):
                    self.routes.append(route)
                else:
                    self.routes.append(
                        {
                            "summary": route.summary,
                            "target": {
                                "ip": route.target.ip,
                                "username": route.target.username,
                                "password": route.target.password.get_secret_value(),
                                "info": route.target.info,
                            },
                            "jumps": [
                                {
                                    "ip": jump.ip,
                                    "username": jump.username,
                                    "password": jump.password.get_secret_value(),
                                    "info": jump.info,
                                }
                                for jump in route.jumps
                            ],
                        }
                    )

            self._reset_host_states()
        except Exception:
            logger.exception("Error loading config")
            self.hosts = []
            self.routes = []
            self.remote_index = None

    def save(self) -> None:
        """Save configuration."""
        try:
            hosts = [
                Host(
                    ip=host["ip"],
                    username=host["username"],
                    password=host["password"],
                    info=host.get("info", ""),
                )
                for host in self.hosts
            ]

            routes = []
            for route in self.routes:
                if isinstance(route, dict):
                    target_host = route.get("target", {})
                    jump_hosts = route.get("jumps", [])

                    target = Host(
                        ip=target_host.get("ip", ""),
                        username=target_host.get("username", ""),
                        password=target_host.get("password", ""),
                        info=target_host.get("info", ""),
                    )
                    jumps = [
                        Host(
                            ip=jump.get("ip", ""),
                            username=jump.get("username", ""),
                            password=jump.get("password", ""),
                            info=jump.get("info", ""),
                        )
                        for jump in jump_hosts
                    ]
                    routes.append(Route(summary=route.get("summary", ""), target=target, jumps=jumps))
                else:
                    routes.append(route)

            config = Configure().load()
            config.networks.hosts = hosts
            config.networks.routes = routes
            Configure().save(config)
        except Exception:
            logger.exception("Error saving config")
            raise

    def _reset_host_states(self) -> None:
        """Reset host states."""
        for host in self.hosts:
            host.setdefault("remote", False)
            host.setdefault("jump", False)
            host.setdefault("jump_order", None)
            host.setdefault("info", "")
        self.remote_index = None

    def add_host(self, host_data: dict[str, Any]) -> None:
        """Add host."""
        self.hosts.append(host_data)
        self._reset_host_states()

    def add_route(self, route_data: dict[str, Any]) -> None:
        """Add route."""
        self.routes.append(route_data)
        self._reset_host_states()

    def delete_host(self, index: int) -> dict[str, Any] | None:
        """Delete host."""
        if 0 <= index < len(self.hosts):
            deleted = self.hosts.pop(index)
            if self.remote_index == index:
                self.remote_index = None
            elif self.remote_index is not None and self.remote_index > index:
                self.remote_index -= 1
            return deleted
        return None

    def delete_route(self, index: int) -> bool:
        """Delete route."""
        if 0 <= index < len(self.routes):
            self.routes.pop(index)
            return True
        return False

    def move_host(self, from_index: int, to_index: int) -> bool:
        """Move host."""
        if 0 <= from_index < len(self.hosts) and 0 <= to_index < len(self.hosts):
            host = self.hosts.pop(from_index)
            self.hosts.insert(to_index, host)
            return True
        return False

    def move_route(self, from_index: int, to_index: int) -> bool:
        """Move route."""
        if 0 <= from_index < len(self.routes) and 0 <= to_index < len(self.routes):
            route = self.routes.pop(from_index)
            self.routes.insert(to_index, route)
            return True
        return False
