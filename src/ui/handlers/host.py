"""
SSH Host Manager - Refactored Implementation
Modular, type-safe SSH host management with clear separation of concerns.
"""

from collections.abc import Callable
import logging
from typing import Any

from nicegui import ui

from src.models.configurations import AppConfig, Host
from src.ui.handlers.host_config import HostConfigManager
from src.ui.handlers.host_ui_state import HostUIState
from src.ui.handlers.host_validator import HostValidator
from src.ui.handlers.route_manager import RouteConnectionManager
from src.ui.handlers.style import CURRENT_THEME, apply_global_theme
from src.utils.connect import Ssh
from src.utils.json import Json

logger = logging.getLogger(__name__)


class HostHandler:
    """Modular SSH Host Manager with clear separation of concerns."""

    def __init__(self) -> None:
        """Initialize the host manager with modular components."""
        logger.debug("Initializing HostHandler")

        # Core components
        self.config = HostConfigManager()
        self.route_connection_manager = RouteConnectionManager()
        self.route_buttons: dict[int, ui.button] = {}
        self.ui_state = HostUIState()

        # Load configuration
        self.config.load()

        # Connection callbacks
        self._on_connection_success: Callable[[], None] | None = None
        self._on_connection_failure: Callable[[], None] | None = None

        # Current SSH connection
        self._current_ssh: Ssh | None = None

        # Styles
        self._styles = CURRENT_THEME

        logger.debug("Starting UI initialization")
        self._init_ui()
        logger.debug("HostHandler initialization complete")

        # Initialize with disconnected state
        self._update_connection_status()

    def _save_config(self) -> None:
        """Save configuration using config manager."""
        self.config.save()

    def _init_ui(self) -> None:
        """Initialize the user interface with proper error handling."""
        try:
            apply_global_theme()
            self._build_main_layout()
            self._refresh_hosts_table()
            self._refresh_routes_table()
        except Exception:
            logger.exception("Failed to initialize UI")
            ui.notify("Failed to initialize interface", color="negative")

    def _build_main_layout(self) -> None:
        """Build the main UI layout."""
        with (
            ui.column().classes("w-full h-screen p-4"),
            ui.card().classes("w-full h-full p-6 shadow-xl bg-gray-50 border border-gray-200"),
        ):
            self._build_header()
            self._build_hosts_section()
            self._build_routes_section()

    def _build_header(self) -> None:
        """Build the header with title and action buttons."""
        with ui.row().classes("w-full justify-center items-center gap-3 mb-6"):
            ui.icon("home", size="lg").classes("text-blue-600")
            ui.label("SSH Host Manager").classes("text-2xl font-bold text-gray-800")
            ui.space()
            ui.button(icon="save", on_click=self._save_config).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            )
            ui.button(icon="download", text="Import", on_click=self._open_import_dialog).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            )
            ui.button(icon="upload", text="Export", on_click=self._export_config).classes(
                "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
            )

    def _build_hosts_section(self) -> None:
        """Build the hosts management section."""
        with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                self.ui_state.hosts_toggle_btn = (
                    ui.button(icon="expand_less", on_click=self._toggle_hosts)
                    .props("flat round")
                    .classes("text-gray-600")
                )
                ui.icon("computer", size="lg").classes("text-blue-600")
                ui.label("Hosts").classes("text-lg font-semibold text-gray-800")
                ui.space()
                ui.button(icon="desktop_windows", text="Add Host", on_click=self._open_add_dialog).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded"
                )
            self.ui_state.table_container = ui.column().classes("w-full")

    def _build_routes_section(self) -> None:
        """Build the routes management section."""
        with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                self.ui_state.routes_toggle_btn = (
                    ui.button(icon="expand_less", on_click=self._toggle_routes)
                    .props("flat round")
                    .classes("text-gray-600")
                )
                ui.icon(name="route", size="lg").classes("text-green-600")
                ui.label("Routes").classes("text-lg font-semibold text-gray-800")
                ui.space()
                self.ui_state.add_route_btn = (
                    ui.button(icon="route", text="Add Route", on_click=self._add_route)
                    .props("disable")
                    .classes("bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")
                )
            self.ui_state.routes_container = ui.column().classes("w-full")

    def _open_add_dialog(self) -> None:
        """Open dialog to add new host with input validation."""
        with ui.dialog() as dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
            ui.label("Add new host").classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Network details").classes("font-semibold mb-3 text-gray-700")
                ip_input = ui.input("IP address", placeholder="192.168.1.100").classes("w-full")
                ip_input.props("outlined").tooltip("Enter the server's IP address")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Authentication").classes("font-semibold mb-3 text-gray-700")
                user_input = ui.input("Username", placeholder="admin").classes("w-full mb-3")
                user_input.props("outlined").tooltip("SSH username for server login")
                pass_input = ui.input("Password", password=True, placeholder="••••••••").classes("w-full")
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
                ).classes("bg-blue-500 hover:bg-blue-600 text-white flex-1")
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 ml-2")

        dialog.open()

    def _add_host(self, ip: str, username: str, password: str, dialog: ui.dialog) -> None:
        """Add new host with validation."""
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

    def _toggle_routes(self) -> None:
        """Toggle routes table visibility."""
        self.ui_state.toggle_routes_expansion()
        self._refresh_routes_table()

    def _delete_host(self, index: int) -> None:
        """Delete host with bounds checking."""
        try:
            deleted_host = self.config.delete_host(index)
            if deleted_host:
                ui.notify(f"Deleted host {deleted_host['ip']}", color="warning")
                self.config.save()
                self._refresh_hosts_table()
        except Exception:
            logger.exception("Error deleting host")

    def _add_route(self) -> None:
        """Add new route with validation."""
        try:
            route_data = self.route_connection_manager.create_route_from_hosts(self.config.hosts)
            if not route_data:
                ui.notify("Please select a remote host first", color="negative")
                return

            if any(r["summary"] == route_data["summary"] for r in self.config.routes):
                ui.notify("Route already exists", color="negative")
                return

            self.config.add_route(route_data)
            self.config.save()

            ui.notify(f"Route added: {route_data['summary']}", color="positive")
            self._refresh_hosts_table()
            self._refresh_routes_table()

        except Exception:
            logger.exception("Error adding route")

    def _toggle_hosts(self) -> None:
        """Toggle hosts table visibility."""
        self.ui_state.toggle_hosts_expansion()
        self._refresh_hosts_table()

    def _delete_route(self, index: int) -> None:
        """Delete route with bounds checking."""
        try:
            if self.config.delete_route(index):
                ui.notify("Route removed", color="warning")
                self.config.save()
                self._refresh_routes_table()
        except Exception:
            logger.exception("Error deleting route")

    def _on_remote_toggle(self, *, checked: bool, index: int) -> None:
        """Handle remote host selection."""
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
                # Reset jump settings for all hosts when unchecking remote
                for host in self.config.hosts:
                    host["jump"] = False
                    host["jump_order"] = None

            self.config.save()
            self._refresh_hosts_table()
        except Exception:
            logger.exception("Error toggling remote host")

    def _on_jump_toggle(self, *, checked: bool, index: int) -> None:
        """Handle jump host selection."""
        try:
            if 0 <= index < len(self.config.hosts):
                self.config.hosts[index]["jump"] = checked
                if not checked:
                    self.config.hosts[index]["jump_order"] = None
                else:
                    # Auto-assign lowest available order when jump is enabled
                    used_orders = {
                        h["jump_order"] for h in self.config.hosts if h["jump_order"] and h != self.config.hosts[index]
                    }
                    for order in range(1, len(self.config.hosts) + 1):
                        if order not in used_orders:
                            self.config.hosts[index]["jump_order"] = order
                            break
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

    def _get_available_orders(self, current_host: dict) -> list[str]:
        """Get available jump orders."""
        return self.config.get_available_jump_orders(current_host)

    def _refresh_hosts_table(self) -> None:
        """Refresh the host management table."""
        if not self.ui_state.table_container:
            return

        try:
            self.ui_state.table_container.clear()
            self.ui_state.host_rows.clear()

            if self.ui_state.hosts_expanded:
                with self.ui_state.table_container:
                    with ui.row().classes(
                        "font-bold text-white bg-gradient-to-r from-blue-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"
                    ):
                        ui.label("").classes("w-6 text-white font-bold")
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("IP Address").classes("w-40 text-white font-bold")
                        ui.label("Username").classes("w-36 text-white font-bold")
                        ui.label("Password").classes("w-36 text-white font-bold")
                        ui.label("Remote").classes("w-28 text-white font-bold")
                        ui.label("Jump").classes("w-24 text-white font-bold")
                        ui.label("Order").classes("w-16 text-center text-white font-bold")
                        ui.label("Actions").classes("w-20 text-center text-white font-bold")

                    for i, host in enumerate(self.config.hosts):
                        self._render_host_row(i, host)

            self._update_add_route_button()

        except Exception:
            logger.exception("Error refreshing table")

    def _render_host_row(self, index: int, host: dict[str, Any]) -> None:
        """Render individual host row."""
        is_remote = host["remote"]
        is_jump = host["jump"]
        is_selected = self.ui_state.selected_host_index == index

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
        self.ui_state.host_rows[index] = row

        # Add click handler to cancel move when clicking outside drag indicator
        row.on("click", lambda e, i=index: self._cancel_host_move_if_outside_drag(e, i))

        with row:
            drag_icon = (
                ui.icon("drag_indicator")
                .classes("text-gray-400 mr-2 cursor-pointer")
                .tooltip("Click to select, then click another row to move")
            )
            drag_icon.on("click", lambda _e, i=index: self._select_host_for_move(i))
            ui.label(str(index + 1)).classes("w-6 text-gray-600 text-left")
            ui.label(host["ip"]).classes("w-40 text-gray-800 text-left")
            ui.label(host["username"]).classes("w-36 text-gray-800 text-left")
            ui.label("••••••").classes("w-36 text-gray-500 text-left")

            cb_remote = ui.checkbox(value=is_remote).classes("w-28 justify-start")
            cb_remote.on_value_change(self._create_remote_handler(index))
            if self.config.remote_index is not None and not is_remote:
                cb_remote.disable()

            cb_jump = ui.checkbox(value=is_jump).classes("w-24 justify-start")
            cb_jump.on_value_change(self._create_jump_handler(index))
            if is_remote:
                cb_jump.disable()

            order_value = str(host["jump_order"]) if host["jump_order"] else None
            order_options = self._get_available_orders(host)
            order_select = ui.select(order_options, value=order_value).props("outlined dense").classes("w-16")
            order_select.on_value_change(self._create_order_handler(index))

            if not is_jump or is_remote:
                order_select.disable()
                order_select.style("box-shadow: none; background: #f3f4f6; border: 1px solid #d1d5db;")

            ui.button(icon="delete", on_click=self._create_delete_handler(index)).props("unelevated").classes(
                "bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded shadow"
            )

    def _refresh_routes_table(self) -> None:
        """Refresh the route table."""
        if not self.ui_state.routes_container:
            return

        try:
            self.ui_state.routes_container.clear()
            self.ui_state.route_rows.clear()

            if self.ui_state.routes_expanded:
                with self.ui_state.routes_container:
                    with ui.row().classes(
                        "font-bold text-white bg-gradient-to-r from-green-600 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"
                    ):
                        ui.label("").classes("w-6 text-white font-bold")
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("Route Summary (Jump → Remote)").classes("flex-1 text-white font-bold text-center")
                        ui.label("Actions").classes("w-40 text-center text-white font-bold")

                    if not self.config.routes:
                        ui.label("No routes defined yet.").classes(
                            "text-gray-500 italic text-center py-4 bg-white border-b border-gray-200"
                        )
                    else:
                        for i, route_data in enumerate(self.config.routes):
                            row_bg = "bg-green-50 border-green-200" if i % 2 else "bg-white border-gray-200"
                            is_selected = self.ui_state.selected_route_index == i
                            if is_selected:
                                row_bg = "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"

                            row = ui.row().classes(
                                f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-green-100"
                            )
                            self.ui_state.route_rows[i] = row

                            # Add click handler to cancel move when clicking outside drag indicator
                            row.on("click", lambda e, idx=i: self._cancel_route_move_if_outside_drag(e, idx))

                            with row:
                                drag_icon = (
                                    ui.icon("drag_indicator")
                                    .classes("text-gray-400 mr-2 cursor-pointer")
                                    .tooltip("Click to select, then click another row to move")
                                )
                                drag_icon.on("click", lambda _e, idx=i: self._select_route_for_move(idx))
                                ui.label(str(i + 1)).classes("w-6 text-gray-600")
                                summary = (
                                    route_data.get("summary", str(route_data))
                                    if isinstance(route_data, dict)
                                    else getattr(route_data, "summary", str(route_data))
                                )
                                ui.label(summary).classes("flex-1 truncate text-gray-800 text-center")
                                with ui.row().classes("gap-2 w-40 justify-center items-center"):
                                    is_connected = self.route_connection_manager.is_connected(i)
                                    btn_color = (
                                        "bg-green-300 hover:bg-green-400 text-green-900"
                                        if is_connected
                                        else "bg-red-300 hover:bg-red-400 text-red-900"
                                    )
                                    icon_name = "power" if is_connected else "power_off"
                                    connect_btn = (
                                        ui.button(icon=icon_name, on_click=self._create_connect_handler(i))
                                        .props("unelevated")
                                        .classes(f"{btn_color} w-16 h-8 rounded shadow")
                                    )
                                    self.route_buttons[i] = connect_btn
                                    ui.button(icon="delete", on_click=self._create_route_delete_handler(i)).props(
                                        "unelevated"
                                    ).classes("bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded shadow")

        except Exception:
            logger.exception("Error refreshing route table")

    def _update_add_route_button(self) -> None:
        """Update add route button state."""
        has_remote = any(h["remote"] for h in self.config.hosts)
        self.ui_state.update_add_route_button(has_remote)

    def _create_remote_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_remote_toggle(checked=e.value, index=index)

    def _create_jump_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_jump_toggle(checked=e.value, index=index)

    def _create_order_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_jump_order_change(e.value, index)

    def _create_delete_handler(self, index: int) -> Callable[[], None]:
        return lambda: self._delete_host(index)

    def _create_route_delete_handler(self, index: int) -> Callable[[], None]:
        return lambda: self._delete_route(index)

    def _create_connect_handler(self, index: int) -> Callable[[], None]:
        return lambda: self._connect_route(index)

    def set_ssh(self, ssh: Ssh | None = None) -> None:
        self._ssh = ssh

    def move_host(self, from_index: int, to_index: int) -> None:
        """Move host from one position to another."""
        if self.config.move_host(from_index, to_index):
            self.ui_state.clear_host_selection()
            self.config.save()
            self._refresh_hosts_table()

    def move_route(self, from_index: int, to_index: int) -> None:
        """Move route from one position to another."""
        if self.config.move_route(from_index, to_index):
            self.ui_state.clear_route_selection()
            self.route_connection_manager.update_connected_indices_after_move(from_index, to_index)
            self.config.save()
            self._refresh_routes_table()

    def _connect_route(self, index: int) -> None:
        """Connect/disconnect route."""
        try:
            if 0 <= index < len(self.config.routes):
                route_data = self.config.routes[index]

                if self.route_connection_manager.is_connected(index):
                    # Disconnect
                    self.route_connection_manager.disconnect_route(index, route_data)
                    self._update_connection_status()
                # Connect
                elif self.route_connection_manager.connect_route(index, route_data):
                    self._update_connection_status()
                    if self._on_connection_success:
                        self._on_connection_success()

                self._refresh_routes_table()
        except Exception:
            logger.exception("Error connecting to route")
            ui.notify("Connection failed", color="negative")

    def _update_connection_status(self) -> None:
        """Update host tab icon color based on connection status."""
        if self.route_connection_manager.connect_route:
            # Green if any connections
            if self._on_connection_success:
                self._on_connection_success()
        # Red if no connections
        elif self._on_connection_failure:
            self._on_connection_failure()

    def _export_config(self) -> None:
        """Export configuration to JSON."""
        try:
            # Convert dictionaries back to Host models for export
            hosts = [
                Host(
                    summary=host.get("summary"),
                    ip=host["ip"],
                    username=host["username"],
                    password=host["password"],
                    remote=host["remote"],
                    jump=host["jump"],
                    jump_order=host.get("jump_order"),
                )
                for host in self.config.hosts
            ]

            app_config = AppConfig(hosts=hosts, routes=self.config.routes)
            config_json = Json.dump_to_string(app_config.model_dump())
            ui.download(config_json.encode(), "ssh_config.json")
            ui.notify("Configuration exported successfully", color="positive")

        except Exception:
            logger.exception("Error exporting config")
            ui.notify("Failed to export configuration", color="negative")

    def _open_import_dialog(self) -> None:
        """Open import dialog."""
        with ui.dialog() as dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
            ui.label("Import configuration").classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Upload file").classes("font-semibold mb-3 text-gray-700")
                ui.upload(on_upload=lambda e: self._handle_file_upload(e, dialog), auto_upload=True).props(
                    'accept=".json"'
                ).classes("w-full")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Paste JSON").classes("font-semibold mb-3 text-gray-700")
                config_input = ui.textarea(placeholder="Paste JSON here...").classes("w-full h-32")

            with ui.row().classes("w-full mt-6"):
                ui.button(
                    icon="download", text="Import", on_click=lambda: self._import_config(config_input.value, dialog)
                ).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg")
                ui.space()
                ui.button(icon="cancel", text="Cancel", on_click=dialog.close).classes(
                    "bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg"
                )
        dialog.open()

    def _handle_file_upload(self, e, dialog: ui.dialog) -> None:
        """Handle file upload."""
        try:
            content = e.content.read().decode("utf-8")
            self._import_config(content, dialog)
        except Exception:
            logger.exception("Error reading file")

    def _import_config(self, config_text: str, dialog: ui.dialog) -> None:
        """Import configuration from JSON."""
        try:
            if not config_text or not config_text.strip():
                ui.notify("Please provide configuration JSON", color="negative")
                return

            config = Json.parse_string(config_text)
            if not isinstance(config, dict) or "hosts" not in config:
                ui.notify("Invalid configuration format", color="negative")
                return

            hosts = config.get("hosts", [])
            routes = config.get("routes", [])

            self.config.hosts = hosts
            self.config.routes = routes if isinstance(routes, list) else []
            self.config.remote_index = None

            # Reset all host selections
            for host in self.config.hosts:
                host["remote"] = False
                host["jump"] = False
                host["jump_order"] = None

            # Reset UI states
            self.ui_state.reset_expansion_states()

            dialog.close()
            self._refresh_hosts_table()
            self._refresh_routes_table()
            ui.notify(f"Imported {len(hosts)} hosts and {len(self.config.routes)} routes", color="positive")

        except ValueError:
            ui.notify("Invalid JSON format", color="negative")
        except Exception:
            logger.exception("Error importing config")

    def _select_host_for_move(self, index: int) -> None:
        """Select host for moving."""
        if self.ui_state.selected_host_index is None:
            self.ui_state.selected_host_index = index
            ui.notify(f"Host {index + 1} selected. Click another host to move.", color="info")
            self._refresh_hosts_table()
        else:
            if self.ui_state.selected_host_index != index:
                self.move_host(self.ui_state.selected_host_index, index)
                ui.notify(
                    f"Moved host {self.ui_state.selected_host_index + 1} to position {index + 1}", color="positive"
                )
            self.ui_state.clear_host_selection()
            self._refresh_hosts_table()

    def _select_route_for_move(self, index: int) -> None:
        """Select route for moving."""
        if self.ui_state.selected_route_index is None:
            self.ui_state.selected_route_index = index
            ui.notify(f"Route {index + 1} selected. Click another route to move.", color="info")
            self._refresh_routes_table()
        else:
            if self.ui_state.selected_route_index != index:
                self.move_route(self.ui_state.selected_route_index, index)
                ui.notify(
                    f"Moved route {self.ui_state.selected_route_index + 1} to position {index + 1}", color="positive"
                )
            self.ui_state.clear_route_selection()
            self._refresh_routes_table()

    def _cancel_host_move_if_outside_drag(self, event: Any, _index: int) -> None:
        """Cancel host move if clicking outside drag indicator."""
        # Check if click target is the drag indicator
        if (
            hasattr(event, "target")
            and "drag_indicator" not in str(event.target)
            and self.ui_state.selected_host_index is not None
        ):
            self.ui_state.clear_host_selection()
            ui.notify("Move operation canceled", color="warning")
            self._refresh_hosts_table()

    def _cancel_route_move_if_outside_drag(self, event: Any, _index: int) -> None:
        """Cancel route move if clicking outside drag indicator."""
        # Check if click target is the drag indicator
        if (
            hasattr(event, "target")
            and "drag_indicator" not in str(event.target)
            and self.ui_state.selected_route_index is not None
        ):
            self.ui_state.clear_route_selection()
            ui.notify("Move operation canceled", color="warning")
            self._refresh_routes_table()
