"""
SSH Host Manager - Fixed Implementation
Clean, working SSH host management with proper structure.
"""

import logging
import re
from typing import Any

from nicegui import ui

from src.core.config import Configure
from src.core.json import Json
from src.core.screen import SingleScreen
from src.models.config import Config, Host, Networks, Route
from src.ui.handlers.host import HostHandler
from src.ui.tabs.base import BasePanel, BaseTab
from src.ui.themes.style import apply_global_theme

logger = logging.getLogger(LogName.MAIN.value)

NAME = "hosts"
LABEL = "Host"
MAX_INPUT_LENGTH = 255


class HostValidator:
    """Validates host-related inputs."""

    _IP_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    _validation_cache: dict[str, bool] = {}

    @classmethod
    def validate_ip(cls, ip: str) -> bool:
        """Validate IP address format with caching."""
        stripped_ip = ip.strip()
        if stripped_ip in cls._validation_cache:
            return cls._validation_cache[stripped_ip]

        result = bool(cls._IP_PATTERN.match(stripped_ip))
        if len(cls._validation_cache) < 100:  # Limit cache size
            cls._validation_cache[stripped_ip] = result
        return result

    @staticmethod
    def sanitize_input(value: str) -> str:
        """Sanitize user input safely."""
        if not isinstance(value, str):
            return ""
        sanitized = value.strip()
        return sanitized if len(sanitized) <= MAX_INPUT_LENGTH else ""

    @staticmethod
    def validate_host_data(
        ip: str, username: str, password: str, existing_hosts: list[dict[str, Any]]
    ) -> str | None:
        """Validate complete host data. Returns error message or None if valid."""
        if not all([ip, username, password]):
            return "All fields are required"

        if not HostValidator.validate_ip(ip):
            return "Invalid IP address format"

        if any(h["ip"] == ip for h in existing_hosts):
            return "IP address already exists"

        return None


class HostTab(BaseTab):
    ICON_NAME: str = "home"

    def __init__(self, *, build: bool = False) -> None:
        super().__init__(NAME, LABEL, self.ICON_NAME)
        if build:
            self.build()

    def build(self) -> None:
        super().build()


class HostPanel(BasePanel, SingleScreen):
    def __init__(
        self,
        config: Config,
        host_handler: HostHandler,
        build: bool = False,
    ):
        BasePanel.__init__(self, NAME, LABEL, HostTab.ICON_NAME)
        SingleScreen.__init__(self)
        self._config = config
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
    """SSH Host Manager with complete functionality."""

    def __init__(self, host_handler: HostHandler) -> None:
        logger.debug("Initializing HostContent")

        # Core components
        self.config = HostConfigManager()
        self.selected_host_index: int | None = None
        self.selected_route_index: int | None = None

        # UI state management
        self.hosts_expanded = True
        self.routes_expanded = True
        self.table_container: ui.column | None = None
        self.routes_container: ui.column | None = None
        self.hosts_toggle_btn: ui.button | None = None
        self.routes_toggle_btn: ui.button | None = None
        self.add_route_btn: ui.button | None = None
        self.host_rows: dict[int, ui.row] = {}
        self.route_rows: dict[int, ui.row] = {}

        # Cached data
        self._cached_remote_hosts: list[dict[str, Any]] | None = None
        self._cached_jump_hosts: list[dict[str, Any]] | None = None
        self._cache_dirty = True

        # Load configuration
        self.config.load()

        # Connection state
        self._host_handler = host_handler

        # Undo state
        self._last_deletion: dict[str, Any] | None = None
        self._undo_btn: ui.button | None = None

    def build(self) -> None:
        """Build method for compatibility."""
        try:
            apply_global_theme()
            self._build_main_layout()
            self._refresh_hosts_table()
            self._refresh_routes_table()
        except Exception:
            logger.exception("Failed to initialize UI")
            ui.notify("Failed to initialize interface", color="negative")

    def _invalidate_cache(self) -> None:
        """Invalidate cached host data."""
        self._cache_dirty = True
        self._cached_remote_hosts = None
        self._cached_jump_hosts = None

    def _get_remote_hosts(self) -> list[dict[str, Any]]:
        """Get cached remote hosts."""
        if self._cache_dirty or self._cached_remote_hosts is None:
            self._cached_remote_hosts = [h for h in self.config.hosts if h.get("remote", False)]
        return self._cached_remote_hosts

    def _get_jump_hosts(self) -> list[dict[str, Any]]:
        """Get cached jump hosts."""
        if self._cache_dirty or self._cached_jump_hosts is None:
            self._cached_jump_hosts = [h for h in self.config.hosts if h.get("jump", False)]
        return self._cached_jump_hosts

    def _build_main_layout(self) -> None:
        """Build the main UI layout."""
        with ui.card().classes("w-full p-4 border"):
            self._build_header()
            self._build_hosts_section()
            self._build_routes_section()

    def _build_header(self) -> None:
        """Build the header."""
        with ui.row().classes("w-full justify-center items-center gap-3 mb-6"):
            ui.icon("home", size="lg").classes("text-blue-600")
            ui.label("SSH Host Manager").classes("text-2xl font-bold text-gray-800")
            ui.space()
            ui.button(icon="save", on_click=self._save_config).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            ).tooltip("Save configuration")
            ui.button(icon="download", on_click=self._open_import_dialog).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            ).tooltip("Import configuration")
            ui.button(icon="upload", on_click=self._export_config).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            ).tooltip("Export configuration")
            self._undo_btn = (
                ui.button(icon="undo", on_click=self._show_undo_dialog)
                .props("disable")
                .classes("bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")
                .tooltip("Undo only lastest deletion")
            )

    def _build_hosts_section(self) -> None:
        """Build the hosts section."""
        with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm p-4"):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                self.hosts_toggle_btn = (
                    ui.button(icon="expand_less", on_click=self._toggle_hosts)
                    .props("flat round")
                    .classes("text-gray-600")
                )
                ui.icon("computer", size="lg").classes("text-blue-600")
                ui.label("Hosts").classes("text-2xl font-semibold text-gray-800")
                ui.space()
                ui.button(
                    icon="desktop_windows", text="Add Host", on_click=self._open_add_dialog
                ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded")
            self.table_container = ui.column().classes("w-full")

    def _build_routes_section(self) -> None:
        """Build the routes section."""
        with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm p-4"):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                self.routes_toggle_btn = (
                    ui.button(icon="expand_less", on_click=self._toggle_routes)
                    .props("flat round")
                    .classes("text-gray-600")
                )
                ui.icon(name="route", size="lg").classes("text-green-600")
                ui.label("Routes").classes("text-2xl font-semibold text-gray-800")
                ui.space()
                self.add_route_btn = (
                    ui.button(icon="route", text="Add Route", on_click=self._add_route)
                    .props("disable")
                    .classes("bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")
                )
            self.routes_container = ui.column().classes("w-full")

    def _save_config(self) -> None:
        """Save configuration."""
        try:
            self.config.save()
            ui.notify("Configuration saved", color="positive")
        except Exception:
            logger.exception("Error saving config")
            ui.notify("Failed to save configuration", color="negative")

    def _open_add_dialog(self) -> None:
        """Open dialog to add new host."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Add new host").classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Network details").classes("font-semibold mb-3 text-gray-700")
                ip_input = ui.input("IP address", placeholder="192.168.1.100").classes("w-full")
                ip_input.props("outlined").tooltip("Enter the server's IP address")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Authentication").classes("font-semibold mb-3 text-gray-700")
                user_input = ui.input("Username", placeholder="admin").classes("w-full mb-3")
                user_input.props("outlined").tooltip("SSH username for server login")
                pass_input = ui.input("Password", password=True, placeholder="••••••••").classes(
                    "w-full"
                )
                pass_input.props("outlined").tooltip("Password for authentication")

            with ui.row().classes("w-full mt-6"):
                ui.button(
                    icon="add",
                    text="Add host",
                    on_click=lambda: self._add_host(
                        HostValidator.sanitize_input(ip_input.value or ""),
                        HostValidator.sanitize_input(user_input.value or ""),
                        HostValidator.sanitize_input(pass_input.value or ""),
                        dialog,
                    ),
                ).classes("bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded")
                ui.space()
                ui.button("Cancel", on_click=dialog.close).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
                )

        dialog.open()

    def _add_host(self, ip: str, username: str, password: str, dialog: ui.dialog) -> None:
        """Add new host."""
        try:
            error_msg = HostValidator.validate_host_data(ip, username, password, self.config.hosts)
            if error_msg:
                ui.notify(error_msg, color="negative")
                return

            new_host: dict[str, Any] = {
                "ip": ip,
                "username": username,
                "password": password,
                "remote": False,
                "jump": False,
                "jump_order": None,
            }

            self.config.add_host(new_host)
            self.config.save()

            dialog.close()
            ui.notify(f"Successfully added host {ip}", color="positive")
            self._refresh_hosts_table()

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

    def _delete_host(self, index: int) -> None:
        """Delete host."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            host_to_delete = self.config.hosts[index]
            host_ip = host_to_delete["ip"]

            # Find affected routes
            affected_routes = []
            for i, route in enumerate(self.config.routes):
                summary = (
                    route.get("summary", "")
                    if isinstance(route, dict)
                    else getattr(route, "summary", "")
                )
                if host_ip in summary:
                    affected_routes.append((i, summary))

            if affected_routes:
                self._show_delete_confirmation(index, host_ip, affected_routes)
            else:
                self._perform_host_deletion(index)
        except Exception:
            logger.exception("Error deleting host")

    def _add_route(self) -> None:
        """Add new route."""
        try:
            # Use cached host data
            remote_hosts = self._get_remote_hosts()
            jump_hosts = self._get_jump_hosts()

            if not remote_hosts:
                ui.notify("Please select a target host first", color="negative")
                return

            # Create route with proper target and jumps
            remote_host = remote_hosts[0]

            # Build summary efficiently
            if jump_hosts:
                # Sort jump hosts by order for consistent summary
                sorted_jumps = sorted(jump_hosts, key=lambda h: h.get("jump_order", 0))
                jump_summary = " ⟶ ".join(h["ip"] for h in sorted_jumps)
                summary = f"{jump_summary} ⟶ {remote_host['ip']} (Target)"
            else:
                summary = f"Direct ⟶ {remote_host['ip']} (Target)"

            # Check for duplicate routes early
            existing_summaries = {
                r.get("summary") if isinstance(r, dict) else getattr(r, "summary", str(r))
                for r in self.config.routes
            }
            if summary in existing_summaries:
                ui.notify("Route already exists", color="negative")
                return

            route_data = {
                "summary": summary,
                "target": {k: remote_host[k] for k in ("ip", "username", "password")},
                "jumps": [
                    {k: jump[k] for k in ("ip", "username", "password")} for jump in jump_hosts
                ],
            }

            self.config.add_route(route_data)
            self.config.save()

            # Reset host selections efficiently
            for host in self.config.hosts:
                host.update({"remote": False, "jump": False, "jump_order": None})
            self.config.remote_index = None
            self._invalidate_cache()

            ui.notify(f"Route added: {summary}", color="positive")
            self._refresh_hosts_table()
            self._refresh_routes_table()
        except Exception:
            logger.exception("Error adding route")

    def _connect_route(self, index: int) -> None:
        """Connect to route."""
        try:
            if 0 <= index < len(self.config.routes):
                route = self.config.routes[index]
                route_summary = (
                    route.get("summary", str(route))
                    if isinstance(route, dict)
                    else getattr(route, "summary", str(route))
                )
                ui.notify(f"Connecting to route: {route_summary}", color="info")

                if self._host_handler.connect_to_route(index):
                    self._refresh_routes_table()
                else:
                    ui.notify("Failed to connect to route", color="negative")
        except Exception:
            logger.exception("Error connecting to route")
            ui.notify("Failed to connect to route", color="negative")

    def _disconnect_route(self, index: int) -> None:
        """Disconnect from route."""
        self._host_handler.disconnect_from_route(index)
        self._refresh_routes_table()

    def _delete_route(self, index: int) -> None:
        """Delete route."""
        try:
            if 0 <= index < len(self.config.routes):
                # Disconnect if connected
                if self._host_handler.is_route_connected(index):
                    self._host_handler.disconnect_from_route(index)

                deleted_route = self.config.routes[index]
                if self.config.delete_route(index):
                    # Store undo state
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

    def _refresh_hosts_table(self) -> None:
        """Refresh the hosts table."""
        if not self.table_container:
            return

        try:
            self.table_container.clear()
            self.host_rows.clear()

            if self.hosts_expanded:
                with self.table_container:
                    # Header row
                    with ui.row().classes(
                        "font-bold text-white bg-gradient-to-r from-blue-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"
                    ):
                        ui.label("Move").classes("w-16 text-center text-white font-bold")
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("IP Address").classes("w-40 text-white font-bold")
                        ui.label("Username").classes("w-36 text-white font-bold")
                        ui.label("Password").classes("w-36 text-white font-bold")
                        ui.label("Target").classes("w-28 text-white font-bold")
                        ui.label("Jump").classes("w-24 text-white font-bold")
                        ui.label("Order").classes("w-16 text-center text-white font-bold")
                        ui.label("Actions").classes("w-20 text-center text-white font-bold")

                    # Data rows
                    for i, host in enumerate(self.config.hosts):
                        self._render_host_row(i, host)

            self._update_add_route_button()
        except Exception:
            logger.exception("Error refreshing hosts table")

    def _render_host_row(self, index: int, host: dict[str, Any]) -> None:
        """Render individual host row."""
        is_remote = host.get("remote", False)
        is_jump = host.get("jump", False)
        # Check if this row is selected for moving
        is_selected = self.selected_host_index == index

        # Row styling
        if is_selected:
            row_bg = "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"
        elif is_remote:
            row_bg = "bg-gradient-to-r from-white to-blue-500 border-blue-400"
        elif is_jump:
            row_bg = "bg-gradient-to-r from-white to-blue-200 border-blue-300"
        elif index % 2:
            row_bg = "bg-gradient-to-r from-white to-gray-50 border-gray-200"
        else:
            row_bg = "bg-gradient-to-r from-white to-white border-gray-200"

        row = ui.row().classes(
            f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-gray-100"
        )
        self.host_rows[index] = row

        with row:
            # Drag handle for reordering
            drag_btn = (
                ui.button(
                    icon="drag_indicator", on_click=lambda i=index: self._select_host_for_move(i)
                )
                .props("flat")
                .classes("text-gray-400 cursor-pointer w-16 justify-center")
            )
            drag_btn.tooltip("Click to select, then click another row to move")

            ui.label(str(index + 1)).classes("w-6 text-gray-600 text-left")
            ui.label(host["ip"]).classes("w-40 text-gray-800 text-left")
            ui.label(host["username"]).classes("w-36 text-gray-800 text-left")
            ui.label("••••••").classes("w-36 text-gray-500 text-left")

            # Target checkbox
            cb_remote = ui.checkbox(value=is_remote).classes("w-28 justify-start")
            cb_remote.on_value_change(
                lambda e, i=index: self._on_remote_toggle(checked=e.value, index=i)
            )
            if getattr(self.config, "remote_index", None) is not None and not is_remote:
                cb_remote.disable()

            # Jump checkbox - disabled if no target selected
            cb_jump = ui.checkbox(value=is_jump).classes("w-24 justify-start")
            cb_jump.on_value_change(
                lambda e, i=index: self._on_jump_toggle(checked=e.value, index=i)
            )
            if is_remote or getattr(self.config, "remote_index", None) is None:
                cb_jump.disable()

            # Jump order select
            order_value = str(host.get("jump_order", "")) if host.get("jump_order") else None
            order_options = self._get_available_orders(host)
            order_select = (
                ui.select(order_options, value=order_value).props("outlined dense").classes("w-16")
            )
            order_select.on_value_change(lambda e, i=index: self._on_jump_order_change(e.value, i))

            if not is_jump or is_remote:
                order_select.disable()

            # Delete button
            ui.button(icon="delete", on_click=lambda i=index: self._delete_host(i)).props(
                "unelevated"
            ).classes("bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded shadow").tooltip(
                "Delete host"
            )

    def _refresh_routes_table(self) -> None:
        """Refresh the routes table."""
        if not self.routes_container:
            return

        try:
            self.routes_container.clear()
            self.route_rows.clear()

            if self.routes_expanded:
                with self.routes_container:
                    # Header row
                    with ui.row().classes(
                        "font-bold text-white bg-gradient-to-r from-green-600 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"
                    ):
                        ui.label("Move").classes("w-16 text-center text-white font-bold")
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("Route Summary").classes("flex-1 text-white font-bold text-center")
                        ui.label("Actions").classes("w-40 text-center text-white font-bold")

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
        """Render individual route row."""
        row_bg = "bg-green-50 border-green-200" if index % 2 else "bg-white border-gray-200"
        is_selected = self.selected_route_index == index
        if is_selected:
            row_bg = "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"

        row = ui.row().classes(
            f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-green-100"
        )
        self.route_rows[index] = row

        with row:
            # Drag handle for reordering
            drag_btn = (
                ui.button(
                    icon="drag_indicator", on_click=lambda i=index: self._select_route_for_move(i)
                )
                .props("flat")
                .classes("text-gray-400 cursor-pointer w-16 justify-center")
            )
            drag_btn.tooltip("Click to select, then click another row to move")

            ui.label(str(index + 1)).classes("w-6 text-gray-600")
            summary = (
                route_data.get("summary", str(route_data))
                if isinstance(route_data, dict)
                else getattr(route_data, "summary", str(route_data))
            )
            ui.label(summary).classes("flex-1 truncate text-gray-800 text-center")

            with ui.row().classes("gap-2 w-40 justify-center items-center"):
                # Connect/Disconnect button
                is_connected = self._host_handler.is_route_connected(index)
                if is_connected:
                    ui.button(
                        icon="power_off", on_click=lambda idx=index: self._disconnect_route(idx)
                    ).props("unelevated").classes(
                        "bg-red-500 hover:bg-red-600 text-white w-16 h-8 rounded shadow"
                    ).tooltip("Disconnect from route")
                else:
                    ui.button(
                        icon="power", on_click=lambda idx=index: self._connect_route(idx)
                    ).props("unelevated").classes(
                        "bg-green-500 hover:bg-green-600 text-white w-16 h-8 rounded shadow"
                    ).tooltip("Connect to route")
                # Delete button
                ui.button(icon="delete", on_click=lambda idx=index: self._delete_route(idx)).props(
                    "unelevated"
                ).classes(
                    "bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded shadow"
                ).tooltip("Delete route")

    def _update_add_route_button(self) -> None:
        """Update add route button state."""
        if not self.add_route_btn:
            return

        has_remote = bool(self._get_remote_hosts())

        if has_remote:
            self.add_route_btn.props(remove="disable").classes(
                remove="bg-gray-100 text-gray-400 cursor-not-allowed"
            ).classes(add="bg-blue-500 hover:bg-blue-600 text-white")
        else:
            self.add_route_btn.props(add="disable").classes(
                add="bg-gray-100 text-gray-400 cursor-not-allowed"
            ).classes(remove="bg-blue-500 hover:bg-blue-600 text-white")

    def _on_remote_toggle(self, *, checked: bool, index: int) -> None:
        """Handle remote host selection."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            if checked:
                # Clear all remote flags efficiently
                for host in self.config.hosts:
                    host["remote"] = False
                # Set this one as remote
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
        """Handle jump host selection."""
        try:
            if not (0 <= index < len(self.config.hosts)):
                return

            host = self.config.hosts[index]
            host["jump"] = checked

            if not checked:
                host["jump_order"] = None
            else:
                # Auto-assign order efficiently
                used_orders = {
                    h.get("jump_order")
                    for h in self.config.hosts
                    if h.get("jump_order") and h != host
                }
                host["jump_order"] = next(
                    (
                        order
                        for order in range(1, len(self.config.hosts) + 1)
                        if order not in used_orders
                    ),
                    1,
                )

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
        # Count non-target hosts (total hosts - 1 target)
        target_count = sum(1 for h in self.config.hosts if h.get("remote", False))
        max_order = len(self.config.hosts) - target_count

        used_orders = {
            h.get("jump_order")
            for h in self.config.hosts
            if h.get("jump_order") and h != current_host
        }
        return [str(j) for j in range(1, max_order + 1) if j not in used_orders]

    def _select_route_for_move(self, index: int) -> None:
        """Select route for moving."""
        if self.selected_route_index == index:
            self.selected_route_index = None
        elif self.selected_route_index is not None:
            # Move route
            self._move_route(self.selected_route_index, index)
            self.selected_route_index = None
        else:
            self.selected_route_index = index
        self._refresh_routes_table()

    def _move_route(self, from_index: int, to_index: int) -> None:
        """Move route from one position to another."""
        try:
            if 0 <= from_index < len(self.config.routes) and 0 <= to_index < len(
                self.config.routes
            ):
                route = self.config.routes.pop(from_index)
                self.config.routes.insert(to_index, route)
                self.config.save()
                ui.notify(
                    f"Moved route from position {from_index + 1} to {to_index + 1}", color="info"
                )
        except Exception:
            logger.exception("Error moving route")

    def _select_host_for_move(self, index: int) -> None:
        """Select host for moving."""
        if self.selected_host_index == index:
            self.selected_host_index = None
        elif self.selected_host_index is not None:
            # Move host
            self._move_host(self.selected_host_index, index)
            self.selected_host_index = None
        else:
            self.selected_host_index = index
        self._refresh_hosts_table()

    def _move_host(self, from_index: int, to_index: int) -> None:
        """Move host from one position to another."""
        try:
            if 0 <= from_index < len(self.config.hosts) and 0 <= to_index < len(self.config.hosts):
                host = self.config.hosts.pop(from_index)
                self.config.hosts.insert(to_index, host)
                self.config.save()
                ui.notify(
                    f"Moved host from position {from_index + 1} to {to_index + 1}", color="info"
                )
                self._refresh_hosts_table()
        except Exception:
            logger.exception("Error moving host")

    def _update_connection_status(self) -> None:
        """Update connection status."""

    def _export_config(self) -> None:
        """Export configuration to JSON."""
        try:
            hosts = [
                Host(
                    ip=h["ip"],
                    username=h["username"],
                    password=h["password"],
                )
                for h in self.config.hosts
            ]

            # Convert dict routes to Route objects for export
            routes = []
            for route in self.config.routes:
                if isinstance(route, dict):
                    target_host = route.get("target", {})
                    jump_hosts = route.get("jumps", [])
                    summary = route.get("summary", "")

                    # If target data is missing, reconstruct from summary and hosts
                    if not target_host.get("ip"):
                        target_host = self._reconstruct_target_from_summary(summary)

                    # If jump data is missing, reconstruct from summary and hosts
                    if not jump_hosts:
                        jump_hosts = self._reconstruct_jumps_from_summary(summary)

                    target = Host(
                        ip=target_host.get("ip", ""),
                        username=target_host.get("username", ""),
                        password=target_host.get("password", ""),
                    )

                    jumps = [
                        Host(
                            ip=jump.get("ip", ""),
                            username=jump.get("username", ""),
                            password=jump.get("password", ""),
                        )
                        for jump in jump_hosts
                    ]

                    routes.append(Route(summary=summary, target=target, jumps=jumps))
                else:
                    routes.append(route)

            app_config = Config(networks=Networks(hosts=hosts, routes=routes))
            config_json = Json.dump_to_string(app_config.model_dump())
            ui.download(config_json.encode(), "ssh_config.json")
            ui.notify("Configuration exported successfully", color="positive")

        except Exception:
            logger.exception("Error exporting config")
            ui.notify("Failed to export configuration", color="negative")

    def _reconstruct_target_from_summary(self, summary: str) -> dict[str, str]:
        """Reconstruct target host data from route summary."""
        # Extract target IP from summary (after last ⟶ and before (Target))
        if "(Target)" in summary:
            target_part = summary.split("(Target)")[0].strip()
            if "⟶" in target_part:
                target_ip = target_part.split("⟶")[-1].strip()
            else:
                # Direct connection
                target_ip = target_part.replace("Direct", "").strip()

            # Find matching host
            for host in self.config.hosts:
                if host["ip"] == target_ip:
                    return {
                        "ip": host["ip"],
                        "username": host["username"],
                        "password": host["password"],
                    }
        return {"ip": "", "username": "", "password": ""}

    def _reconstruct_jumps_from_summary(self, summary: str) -> list[dict[str, str]]:
        """Reconstruct jump hosts data from route summary."""
        if "Direct" in summary or "⟶" not in summary:
            return []

        # Extract jump IPs (everything before last ⟶)
        parts = summary.split("⟶")
        if len(parts) < 2:
            return []

        jump_ips = []
        for part in parts[:-1]:  # All parts except the last (target)
            ip = part.strip()
            if ip and ip != "Direct":
                jump_ips.append(ip)

        # Find matching hosts
        jumps = []
        for jump_ip in jump_ips:
            for host in self.config.hosts:
                if host["ip"] == jump_ip:
                    jumps.append(
                        {
                            "ip": host["ip"],
                            "username": host["username"],
                            "password": host["password"],
                        }
                    )
                    break
        return jumps

    def _update_undo_button(self) -> None:
        """Update undo button state."""
        if not self._undo_btn:
            return

        if self._last_deletion:
            self._undo_btn.props(remove="disable").classes(
                remove="bg-gray-100 text-gray-400 cursor-not-allowed"
            ).classes(add="bg-blue-500 hover:bg-blue-600 text-white")
        else:
            self._undo_btn.props(add="disable").classes(
                add="bg-gray-100 text-gray-400 cursor-not-allowed"
            ).classes(remove="bg-blue-500 hover:bg-blue-600 text-white")

    def _show_undo_dialog(self) -> None:
        """Show undo confirmation dialog."""
        if not self._last_deletion:
            return

        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Undo Last Deletion").classes(
                "text-xl font-bold mb-4 text-center text-gray-800"
            )

            host_data = self._last_deletion["host"]
            routes_data = self._last_deletion["routes"]

            ui.label("This will restore:").classes("text-gray-700 mb-2")

            with ui.column().classes("w-full mb-4"):
                if host_data:
                    ui.label(f"• Host: {host_data['data']['ip']}").classes("text-sm text-gray-600")

                if routes_data:
                    ui.label(f"• {len(routes_data)} route(s):").classes("text-sm text-gray-600")
                    for _, route in routes_data:
                        summary = (
                            route.get("summary", str(route))
                            if isinstance(route, dict)
                            else getattr(route, "summary", str(route))
                        )
                        ui.label(f"  - {summary}").classes("text-xs text-gray-500 ml-4")

            with ui.row().classes("w-full gap-2"):
                ui.button("Restore", on_click=lambda: self._perform_undo(dialog)).classes(
                    "bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
                )

                ui.button("Cancel", on_click=dialog.close).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                )

        dialog.open()

    def _perform_undo(self, dialog: ui.dialog) -> None:
        """Perform the undo operation."""
        try:
            if not self._last_deletion:
                return

            host_data = self._last_deletion["host"]
            routes_data = self._last_deletion["routes"]

            # Restore host
            if host_data:
                host_index = min(host_data["index"], len(self.config.hosts))
                self.config.hosts.insert(host_index, host_data["data"])

            # Restore routes
            for route_index, route_data in routes_data:
                restore_index = min(route_index, len(self.config.routes))
                self.config.routes.insert(restore_index, route_data)

            # Clear undo state
            self._last_deletion = None
            self._update_undo_button()

            dialog.close()

            # Save and refresh
            self.config.save()
            self._refresh_hosts_table()
            self._refresh_routes_table()

            restored_items = []
            if host_data:
                restored_items.append(f"host {host_data['data']['ip']}")
            if routes_data:
                restored_items.append(f"{len(routes_data)} route(s)")

            ui.notify(f"Restored {' and '.join(restored_items)}", color="positive")

        except Exception:
            logger.exception("Error performing undo")
            ui.notify("Failed to undo deletion", color="negative")

    def _show_delete_confirmation(
        self, host_index: int, host_ip: str, affected_routes: list[tuple[int, str]]
    ) -> None:
        """Show confirmation dialog for host deletion with affected routes."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label(f"Delete host {host_ip}?").classes(
                "text-xl font-bold mb-4 text-center text-gray-800"
            )

            ui.label(f"This host is used in {len(affected_routes)} route(s):").classes(
                "text-gray-700 mb-2"
            )

            with ui.column().classes("w-full mb-4 max-h-32 overflow-y-auto"):
                for _, summary in affected_routes:
                    ui.label(f"• {summary}").classes("text-sm text-gray-600")

            ui.label("Do you want to remove the affected routes too?").classes("text-gray-700 mb-4")

            with ui.row().classes("w-full gap-2"):
                ui.button(
                    "Remove All",
                    on_click=lambda: self._delete_host_and_routes(
                        host_index, affected_routes, dialog
                    ),
                ).classes("bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded")

                ui.button(
                    "Host Only", on_click=lambda: self._perform_host_deletion(host_index, dialog)
                ).classes("bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded")

                ui.button("Cancel", on_click=dialog.close).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
                )

        dialog.open()

    def _delete_host_and_routes(
        self, host_index: int, affected_routes: list[tuple[int, str]], dialog: ui.dialog
    ) -> None:
        """Delete host and all affected routes."""
        try:
            # Store deletion state for undo
            deleted_routes = []
            route_indices = sorted([i for i, _ in affected_routes], reverse=True)

            # Collect route data before deletion
            for route_index in route_indices:
                if 0 <= route_index < len(self.config.routes):
                    deleted_routes.append((route_index, self.config.routes[route_index]))

            # Delete routes first
            for route_index in route_indices:
                self.config.delete_route(route_index)

            # Then delete host
            deleted_host = self.config.delete_host(host_index)

            # Store undo state
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
                self._refresh_hosts_table()
                self._refresh_routes_table()
        except Exception:
            logger.exception("Error deleting host and routes")
            ui.notify("Failed to delete host and routes", color="negative")

    def _perform_host_deletion(self, host_index: int, dialog: ui.dialog | None = None) -> None:
        """Perform the actual host deletion."""
        try:
            deleted_host = self.config.delete_host(host_index)

            # Store undo state
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
            ui.notify("Failed to delete host", color="negative")

    def _open_import_dialog(self) -> None:
        """Open import dialog."""
        with (
            ui.dialog() as dialog,
            ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"),
        ):
            ui.label("Import configuration").classes(
                "text-xl font-bold mb-6 text-center text-gray-800"
            )

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Upload JSON File").classes("font-semibold mb-3 text-gray-700")
                file_upload = (
                    ui.upload(
                        on_upload=lambda e: self._handle_file_upload(e, dialog), auto_upload=True
                    )
                    .props("accept=.json")
                    .classes("w-full")
                )

            ui.label("OR").classes("text-center text-gray-500 font-bold my-2")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Paste JSON").classes("font-semibold mb-3 text-gray-700")
                config_input = ui.textarea(placeholder="Paste JSON here...").classes("w-full h-32")

            with ui.row().classes("w-full mt-6"):
                ui.button(
                    icon="download",
                    text="Import",
                    on_click=lambda: self._import_config(config_input.value, dialog),
                ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg")
                ui.space()
                ui.button(icon="cancel", text="Cancel", on_click=dialog.close).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg"
                )
        dialog.open()

    def _import_config(self, config_text: str, dialog: ui.dialog) -> None:
        """Import configuration from JSON."""
        try:
            if not config_text or not config_text.strip():
                ui.notify("Please provide configuration JSON", color="negative")
                return

            config = Json.parse_string(config_text)
            if not isinstance(config, dict):
                ui.notify("Invalid configuration format", color="negative")
                return

            # Handle both direct format and nested networks format
            if "networks" in config:
                networks = config["networks"]
                hosts = networks.get("hosts", [])
                routes = networks.get("routes", [])
            elif "hosts" in config:
                hosts = config.get("hosts", [])
                routes = config.get("routes", [])
            else:
                ui.notify("No hosts found in configuration", color="negative")
                return

            # Count totals and filter duplicates
            total_hosts = len(hosts)
            total_routes = len(routes) if isinstance(routes, list) else 0

            # Import only new hosts
            new_hosts = []
            existing_ips = {h["ip"] for h in self.config.hosts}
            for host in hosts:
                if host.get("ip") not in existing_ips:
                    new_hosts.append(host)
                    self.config.hosts.append(host)

            # Import only new routes
            new_routes = []
            existing_summaries = {r.get("summary", str(r)) for r in self.config.routes}
            for route in routes if isinstance(routes, list) else []:
                route_summary = route.get("summary", str(route))
                if route_summary not in existing_summaries:
                    new_routes.append(route)
                    self.config.routes.append(route)

            # Reset all host selections
            for host in self.config.hosts:
                host["remote"] = False
                host["jump"] = False
                host["jump_order"] = None

            self.config.remote_index = None
            self.hosts_expanded = True
            self.routes_expanded = True

            dialog.close()
            self._refresh_hosts_table()
            self._refresh_routes_table()

            # Provide detailed feedback
            new_host_count = len(new_hosts)
            new_route_count = len(new_routes)
            duplicate_hosts = total_hosts - new_host_count
            duplicate_routes = total_routes - new_route_count

            if new_host_count > 0 or new_route_count > 0:
                message = f"Imported {new_host_count} new hosts and {new_route_count} new routes"
                if duplicate_hosts > 0 or duplicate_routes > 0:
                    message += f" (skipped {duplicate_hosts} duplicate hosts, {duplicate_routes} duplicate routes)"
                ui.notify(message, color="positive")
            else:
                ui.notify(
                    f"No new items imported - all {total_hosts} hosts and {total_routes} routes already exist",
                    color="info",
                )

        except ValueError:
            ui.notify("Invalid JSON format", color="negative")
        except Exception:
            logger.exception("Error importing config")
            ui.notify("Import failed", color="negative")

    def _handle_file_upload(self, e, dialog: ui.dialog) -> None:
        """Handle file upload for import."""
        try:
            if not e.content:
                ui.notify("No file content received", color="negative")
                return

            # Decode file content
            config_text = e.content.read().decode("utf-8")
            self._import_config(config_text, dialog)

        except Exception:
            logger.exception("Error handling file upload")
            ui.notify("Failed to read uploaded file", color="negative")

    def _select_host_for_move(self, index: int) -> None:
        """Select host for moving."""
        if self.selected_host_index is None:
            self.selected_host_index = index
            ui.notify(f"Host {index + 1} selected. Click another host to move.", color="info")
            self._refresh_hosts_table()
        else:
            if self.selected_host_index != index:
                self._move_host(self.selected_host_index, index)
                ui.notify(
                    f"Moved host {self.selected_host_index + 1} to position {index + 1}",
                    color="positive",
                )
            self.selected_host_index = None
            self._refresh_hosts_table()

    def _select_route_for_move(self, index: int) -> None:
        """Select route for moving."""
        if self.selected_route_index is None:
            self.selected_route_index = index
            ui.notify(f"Route {index + 1} selected. Click another route to move.", color="info")
            self._refresh_routes_table()
        else:
            if self.selected_route_index != index:
                self._move_route(self.selected_route_index, index)
                ui.notify(
                    f"Moved route {self.selected_route_index + 1} to position {index + 1}",
                    color="positive",
                )
            self.selected_route_index = None
            self._refresh_routes_table()

    def _move_host(self, from_index: int, to_index: int) -> None:
        """Move host from one position to another."""
        if self.config.move_host(from_index, to_index):
            self.config.save()

    def _move_route(self, from_index: int, to_index: int) -> None:
        """Move route from one position to another."""
        if self.config.move_route(from_index, to_index):
            self.config.save()


class HostConfigManager:
    """Manages host and route configuration."""

    def __init__(self) -> None:
        self.hosts: list[dict[str, Any]] = []
        self.routes: list[dict[str, Any]] = []
        self.remote_index: int | None = None

    def load(self) -> None:
        """Load configuration from file."""
        try:
            config = Configure().load()
            self.hosts = [
                {
                    "ip": host.ip,
                    "username": host.username,
                    "password": host.password.get_secret_value(),
                }
                for host in config.networks.hosts
            ]
            # Convert Route objects to dicts for internal use
            self.routes = []
            for route in config.networks.routes:
                if isinstance(route, dict):
                    self.routes.append(route)
                else:
                    # Convert Route object to dict with full data
                    route_dict = {
                        "summary": route.summary,
                        "target": {
                            "ip": route.target.ip,
                            "username": route.target.username,
                            "password": route.target.password.get_secret_value(),
                        },
                        "jumps": [
                            {
                                "ip": jump.ip,
                                "username": jump.username,
                                "password": jump.password.get_secret_value(),
                            }
                            for jump in route.jumps
                        ],
                    }
                    self.routes.append(route_dict)
            self._reset_host_states()
            logger.debug("Loaded %d hosts and %d routes", len(self.hosts), len(self.routes))
        except Exception:
            logger.exception("Error loading config")
            self._use_defaults()

    def save(self) -> None:
        """Save configuration to file."""
        try:
            hosts = [
                Host(
                    ip=host["ip"],
                    username=host["username"],
                    password=host["password"],
                )
                for host in self.hosts
            ]

            # Convert dict routes to Route objects
            routes = []
            for route in self.routes:
                if isinstance(route, dict):
                    # Find target and jump hosts from route data
                    target_host = route.get("target", {})
                    jump_hosts = route.get("jumps", [])

                    target = Host(
                        ip=target_host.get("ip", ""),
                        username=target_host.get("username", ""),
                        password=target_host.get("password", ""),
                    )

                    jumps = [
                        Host(
                            ip=jump.get("ip", ""),
                            username=jump.get("username", ""),
                            password=jump.get("password", ""),
                        )
                        for jump in jump_hosts
                    ]

                    routes.append(
                        Route(summary=route.get("summary", ""), target=target, jumps=jumps)
                    )
                else:
                    routes.append(route)

            config = Configure().load()
            config.networks.hosts = hosts
            config.networks.routes = routes
            Configure().save(config)
        except Exception:
            logger.exception("Error saving config")
            raise

    def _use_defaults(self) -> None:
        """Initialize with empty configuration."""
        self.hosts = []
        self.routes = []
        self.remote_index = None

    def _reset_host_states(self) -> None:
        """Reset all host states."""
        for host in self.hosts:
            host.setdefault("remote", False)
            host.setdefault("jump", False)
            host.setdefault("jump_order", None)
        self.remote_index = None

    def add_host(self, host_data: dict[str, Any]) -> None:
        """Add new host."""
        self.hosts.append(host_data)
        self._reset_host_states()

    def batch_update_hosts(self, updates: list[tuple[int, dict[str, Any]]]) -> None:
        """Batch update multiple hosts efficiently."""
        for index, update_data in updates:
            if 0 <= index < len(self.hosts):
                self.hosts[index].update(update_data)

    def get_available_jump_orders(self, current_host: dict) -> list[str]:
        """Get available jump orders for host."""
        # Count non-target hosts (total hosts - 1 target)
        target_count = sum(1 for h in self.hosts if h.get("remote", False))
        max_order = len(self.hosts) - target_count

        used_orders = {
            h.get("jump_order") for h in self.hosts if h.get("jump_order") and h != current_host
        }
        return [str(j) for j in range(1, max_order + 1) if j not in used_orders]

    def delete_host(self, index: int) -> dict[str, Any] | None:
        """Delete host by index."""
        if 0 <= index < len(self.hosts):
            deleted = self.hosts.pop(index)
            if self.remote_index == index:
                self.remote_index = None
            elif self.remote_index is not None and self.remote_index > index:
                self.remote_index -= 1
            return deleted
        return None

    def add_route(self, route_data: dict[str, Any]) -> None:
        """Add new route."""
        self.routes.append(route_data)
        self._reset_host_states()

    def delete_route(self, index: int) -> bool:
        """Delete route by index."""
        if 0 <= index < len(self.routes):
            self.routes.pop(index)
            return True
        return False

    def move_host(self, from_index: int, to_index: int) -> bool:
        """Move host from one position to another."""
        if 0 <= from_index < len(self.hosts) and 0 <= to_index < len(self.hosts):
            host = self.hosts.pop(from_index)
            self.hosts.insert(to_index, host)
            return True
        return False

    def move_route(self, from_index: int, to_index: int) -> bool:
        """Move route from one position to another."""
        if 0 <= from_index < len(self.routes) and 0 <= to_index < len(self.routes):
            route = self.routes.pop(from_index)
            self.routes.insert(to_index, route)
            return True
        return False
