"""
SSH Host Manager - Optimized Implementation
Type-safe, secure, and performant SSH host management with route configuration.
"""

from collections.abc import Callable
from dataclasses import dataclass
import json
import logging
from pathlib import Path
import re
from typing import Any, TypedDict

from nicegui import ui

from src.utils.ssh_connection import SshConnection

# Constants
MAX_INPUT_LENGTH = 255
CONFIG_DIR = ".interface-check"
CONFIG_FILE = "ssh_config.json"


class HostDict(TypedDict):
    """Type definition for host configuration."""

    ip: str
    username: str
    password: str
    remote: bool
    jump: bool
    jump_order: int | None


class RouteDict(TypedDict):
    """Type definition for route configuration."""

    summary: str
    remote_host_ip: str
    remote_host_username: str
    remote_host_password: str
    jump_hosts: list[dict[str, Any]]


@dataclass(frozen=True)
class UIStyles:
    """Immutable UI styling configuration."""

    header_gradient: str = "font-bold text-white bg-gradient-to-r from-blue-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md"
    route_header_gradient: str = "font-bold text-white bg-gradient-to-r from-green-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md"
    delete_button: str = "bg-red-300 hover:bg-red-400 text-red-900 w-20 h-8 rounded shadow"
    connect_button: str = "bg-green-300 hover:bg-green-400 text-green-900 w-20 h-8 rounded shadow"


class HostHandler:
    """Optimized SSH Host Manager with type safety and error handling."""

    def __init__(self) -> None:
        """Initialize the host manager with default configuration."""
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing HostManager")
        self._load_config()
        self._remote_index: int | None = None
        self._styles = UIStyles()

        # UI components
        self.add_route_btn: ui.button | None = None
        self.table_container: ui.column | None = None
        self.route_container: ui.column | None = None
        self.hosts_toggle_btn: ui.button | None = None
        self.routes_toggle_btn: ui.button | None = None
        self.hosts_expanded: bool = True
        self.routes_expanded: bool = True
        self._on_connection_success: Callable[[], None] | None = None
        self._on_connection_failure: Callable[[], None] | None = None
        self._ssh_connection: SshConnection | None = None
        self._connected_routes: set[int] = set()
        self._route_buttons: dict[int, ui.button] = {}

        # Drag and drop state
        self._selected_host: int | None = None
        self._selected_route: int | None = None
        self._host_rows: dict[int, ui.row] = {}
        self._route_rows: dict[int, ui.row] = {}

        self._logger.debug("Starting UI initialization")
        self._init_ui()
        self._logger.debug("HostManager initialization complete")

        # Initialize with red icon (disconnected state)
        self._update_connection_status()

    def _load_config(self) -> None:
        """Load configuration from ssh_config.json."""
        try:
            config_path = Path.home() / CONFIG_DIR / CONFIG_FILE
            if config_path.exists():
                with config_path.open() as f:
                    config = json.load(f)
                self._validate_config(config)
                self._hosts = config.get("hosts", [])
                self._routes = config.get("routes", [])
                self._reset_host_states()
                self._logger.debug("Loaded %d hosts and %d routes", len(self._hosts), len(self._routes))
            else:
                self._use_default_config()
        except json.JSONDecodeError:
            self._logger.exception("Invalid JSON in config")
            self._use_default_config()
        except PermissionError:
            self._logger.exception("Permission denied accessing config")
            self._use_default_config()
        except Exception:
            self._logger.exception("Unexpected error loading config")
            self._use_default_config()

    def _save_to_file(self) -> None:
        """Save current state to ssh_config.json."""
        try:
            config_dir = Path.home() / CONFIG_DIR
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / CONFIG_FILE

            config = {"hosts": self._hosts, "routes": self._routes}
            with config_path.open("w") as f:
                json.dump(config, f, indent=2)
        except PermissionError:
            self._logger.exception("Permission denied saving config")
            ui.notify("Permission denied saving configuration", color="negative")
        except Exception:
            self._logger.exception("Error saving to file")
            ui.notify("Failed to save configuration", color="negative")

    def _init_ui(self) -> None:
        """Initialize the user interface with proper error handling."""
        try:
            ui.colors(
                primary="#374151",
                secondary="#4b5563",
                accent="#3b82f6",
                dark="#1f2937",
                positive="#10b981",
                negative="#ef4444",
                info="#3b82f6",
                warning="#f59e0b",
            )

            with (
                ui.column().classes("w-full h-screen p-4"),
                ui.card().classes("w-full h-full p-6 shadow-xl bg-gray-50 border border-gray-200"),
            ):
                with ui.row().classes("w-full justify-center items-center gap-3 mb-6"):
                    ui.icon("terminal", size="lg").classes("text-yellow-500")
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

                with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-2 mb-4"):
                        self.hosts_toggle_btn = (
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
                    self.table_container = ui.column().classes("w-full")

                with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-2 mb-4"):
                        self.routes_toggle_btn = (
                            ui.button(icon="expand_less", on_click=self._toggle_routes)
                            .props("flat round")
                            .classes("text-gray-600")
                        )
                        ui.icon("route", size="lg").classes("text-green-600")
                        ui.label("Routes").classes("text-lg font-semibold text-gray-800")
                        ui.space()
                        self.add_route_btn = (
                            ui.button(icon="route", text="Add Route", on_click=self._add_route)
                            .props("disable")
                            .classes("bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")
                        )
                    self.route_container = ui.column().classes("w-full")

            self._refresh_table()
            self._refresh_route_table()

        except Exception:
            self._logger.exception("Failed to initialize UI")
            ui.notify("Failed to initialize interface", color="negative")

    def _validate_config(self, config: dict) -> None:
        """Validate configuration structure."""
        if not isinstance(config, dict):
            msg = "Config must be a dictionary"
            raise TypeError(msg)
        if "hosts" in config and not isinstance(config["hosts"], list):
            msg = "Hosts must be a list"
            raise TypeError(msg)
        if "routes" in config and not isinstance(config["routes"], list):
            msg = "Routes must be a list"
            raise TypeError(msg)

    def _use_default_config(self) -> None:
        """Initialize with default empty configuration."""
        self._hosts = []
        self._routes = []
        self._remote_index = None

    def _reset_host_states(self) -> None:
        """Reset all host states on load."""
        for host in self._hosts:
            host["remote"] = False
            host["jump"] = False
            host["jump_order"] = None
        self._remote_index = None

    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        return bool(re.match(pattern, ip.strip()))

    def _validate_and_sanitize_input(self, value: str, max_length: int = MAX_INPUT_LENGTH) -> str:
        """Validate and sanitize user input."""
        if not isinstance(value, str):
            msg = "Input must be string"
            raise TypeError(msg)
        sanitized = value.strip()
        if len(sanitized) > max_length:
            msg = f"Input too long (max {max_length})"
            raise ValueError(msg)
        return sanitized

    def _sanitize_input(self, value: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        try:
            return self._validate_and_sanitize_input(value)
        except ValueError:
            return ""

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
                        self._sanitize_input(ip_input.value or ""),
                        self._sanitize_input(user_input.value or ""),
                        self._sanitize_input(pass_input.value or ""),
                        dialog,
                    ),
                ).classes("bg-blue-500 hover:bg-blue-600 text-white flex-1")
                ui.button("Cancel", on_click=dialog.close).classes("bg-gray-300 hover:bg-gray-400 text-gray-800 ml-2")

        dialog.open()

    def _add_host(self, ip: str, username: str, password: str, dialog: ui.dialog) -> None:
        """Add new host with comprehensive validation."""
        try:
            if not all([ip, username, password]):
                ui.notify("All fields are required", color="negative")
                return

            if not self._validate_ip(ip):
                ui.notify("Invalid IP address format", color="negative")
                return

            if any(h["ip"] == ip for h in self._hosts):
                ui.notify("IP address already exists", color="negative")
                return

            new_host: HostDict = {
                "ip": ip,
                "username": username,
                "password": password,
                "remote": False,
                "jump": False,
                "jump_order": None,
            }
            self._hosts.append(new_host)
            # Reset all host states after adding
            for host in self._hosts:
                host["remote"] = False
                host["jump"] = False
                host["jump_order"] = None
            self._remote_index = None
            self._save_to_file()

            dialog.close()
            ui.notify(f"Successfully added host {ip}", color="positive")
            self._refresh_table()

        except Exception:
            self._logger.exception("Error adding host")
            ui.notify("Failed to add host", color="negative")

    def _toggle_routes(self) -> None:
        """Toggle routes table visibility."""
        self.routes_expanded = not self.routes_expanded
        if self.routes_toggle_btn:
            icon = "expand_less" if self.routes_expanded else "expand_more"
            self.routes_toggle_btn.props(f'icon="{icon}"')
        self._refresh_route_table()

    def _delete_host(self, index: int) -> None:
        """Delete host with bounds checking."""
        try:
            if not (0 <= index < len(self._hosts)):
                return

            deleted_host = self._hosts.pop(index)
            if self._remote_index == index:
                self._remote_index = None
            elif self._remote_index is not None and self._remote_index > index:
                self._remote_index -= 1

            ui.notify(f"Deleted host {deleted_host['ip']}", color="warning")
            self._save_to_file()
            self._refresh_table()

        except Exception:
            self._logger.exception("Error deleting host")

    def _add_route(self) -> None:
        """Add new route with validation."""
        try:
            remote_host = next((h for h in self._hosts if h["remote"]), None)
            if not remote_host:
                ui.notify("Please select a remote host first", color="negative")
                return

            jump_hosts = sorted(
                [h for h in self._hosts if h["jump"] and h["jump_order"]], key=lambda x: x["jump_order"] or 0
            )

            jump_parts = [f"{h['ip']}(J{h['jump_order']})" for h in jump_hosts]
            remote_part = f"{remote_host['ip']}(Remote)"
            summary = " ⟶ ".join([*jump_parts, remote_part])

            if any(r["summary"] == summary for r in self._routes):
                ui.notify("Route already exists", color="negative")
                return

            route = {
                "summary": summary,
                "remote_host_ip": remote_host["ip"],
                "remote_host_username": remote_host["username"],
                "remote_host_password": remote_host["password"],
                "jump_hosts": [
                    {"ip": h["ip"], "username": h["username"], "password": h["password"], "order": h["jump_order"]}
                    for h in jump_hosts
                ],
            }
            self._routes.append(route)
            # Reset all host states after adding route
            for host in self._hosts:
                host["remote"] = False
                host["jump"] = False
                host["jump_order"] = None
            self._remote_index = None
            self._save_to_file()
            ui.notify(f"Route added: {summary}", color="positive")
            self._refresh_table()
            self._refresh_route_table()

        except Exception:
            self._logger.exception("Error adding route")

    def _toggle_hosts(self) -> None:
        """Toggle hosts table visibility."""
        self.hosts_expanded = not self.hosts_expanded
        if self.hosts_toggle_btn:
            icon = "expand_less" if self.hosts_expanded else "expand_more"
            self.hosts_toggle_btn.props(f'icon="{icon}"')
        self._refresh_table()

    def _delete_route(self, index: int) -> None:
        """Delete route with bounds checking."""
        try:
            if 0 <= index < len(self._routes):
                self._routes.pop(index)
                self._save_to_file()
                ui.notify("Route removed", color="warning")
                self._refresh_route_table()
        except Exception:
            self._logger.exception("Error deleting route")

    def _on_remote_toggle(self, *, checked: bool, index: int) -> None:
        """Handle remote host selection."""
        try:
            if not (0 <= index < len(self._hosts)):
                return

            if checked:
                for host in self._hosts:
                    host["remote"] = False
                self._hosts[index]["remote"] = True
                self._remote_index = index
            else:
                self._remote_index = None
                self._hosts[index]["remote"] = False
                # Reset jump settings for all hosts when unchecking remote
                for host in self._hosts:
                    host["jump"] = False
                    host["jump_order"] = None

            self._save_to_file()
            self._refresh_table()
        except Exception:
            self._logger.exception("Error toggling remote host")

    def _on_jump_toggle(self, *, checked: bool, index: int) -> None:
        """Handle jump host selection."""
        try:
            if 0 <= index < len(self._hosts):
                self._hosts[index]["jump"] = checked
                if not checked:
                    self._hosts[index]["jump_order"] = None
                else:
                    # Auto-assign lowest available order when jump is enabled
                    used_orders = {h["jump_order"] for h in self._hosts if h["jump_order"] and h != self._hosts[index]}
                    for order in range(1, len(self._hosts) + 1):
                        if order not in used_orders:
                            self._hosts[index]["jump_order"] = order
                            break
                self._save_to_file()
                self._refresh_table()
        except Exception:
            self._logger.exception("Error toggling jump host")

    def _on_jump_order_change(self, value: str, index: int) -> None:
        """Handle jump order change."""
        try:
            if 0 <= index < len(self._hosts):
                order = None
                if value and value.strip():
                    try:
                        order = int(value)
                        if order < 1:
                            order = None
                    except ValueError:
                        order = None
                self._hosts[index]["jump_order"] = order
                self._save_to_file()
        except Exception:
            self._logger.exception("Error updating jump order")

    def _get_available_orders(self, current_host: HostDict) -> list[str]:
        """Get available jump orders."""
        used_orders = {h["jump_order"] for h in self._hosts if h["jump_order"] and h != current_host}
        return [str(j) for j in range(1, len(self._hosts)) if j not in used_orders]

    def _refresh_table(self) -> None:
        """Refresh the host management table."""
        if not self.table_container:
            return

        try:
            self.table_container.clear()
            self._host_rows.clear()

            if self.hosts_expanded:
                with self.table_container:
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

                    for i, host in enumerate(self._hosts):
                        self._render_host_row(i, host)

            self._update_route_button()

        except Exception:
            self._logger.exception("Error refreshing table")

    def _render_host_row(self, index: int, host: HostDict) -> None:
        """Render individual host row."""
        is_remote = host["remote"]
        is_jump = host["jump"]
        is_selected = self._selected_host == index

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
        self._host_rows[index] = row

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
            if self._remote_index is not None and not is_remote:
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

    def _refresh_route_table(self) -> None:
        """Refresh the route table."""
        if not self.route_container:
            return

        try:
            self.route_container.clear()
            self._route_rows.clear()

            if self.routes_expanded:
                with self.route_container:
                    with ui.row().classes(
                        "font-bold text-white bg-gradient-to-r from-green-600 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"
                    ):
                        ui.label("").classes("w-6 text-white font-bold")
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("Route Summary (Jump → Remote)").classes("flex-1 text-white font-bold text-center")
                        ui.label("Actions").classes("w-40 text-center text-white font-bold")

                    if not self._routes:
                        ui.label("No routes defined yet.").classes(
                            "text-gray-500 italic text-center py-4 bg-white border-b border-gray-200"
                        )
                    else:
                        for i, route in enumerate(self._routes):
                            row_bg = "bg-green-50 border-green-200" if i % 2 else "bg-white border-gray-200"
                            is_selected = self._selected_route == i
                            if is_selected:
                                row_bg = "bg-gradient-to-r from-blue-100 to-blue-200 border-blue-400"
                            else:
                                row_bg = "bg-green-50 border-green-200" if i % 2 else "bg-white border-gray-200"

                            row = ui.row().classes(
                                f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-green-100"
                            )
                            self._route_rows[i] = row

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
                                ui.label(route["summary"]).classes("flex-1 truncate text-gray-800 text-center")
                                with ui.row().classes("gap-2 w-40 justify-center items-center"):
                                    btn_color = (
                                        "bg-green-300 hover:bg-green-400 text-green-900"
                                        if i in self._connected_routes
                                        else "bg-red-300 hover:bg-red-400 text-red-900"
                                    )
                                    icon_name = "power" if i in self._connected_routes else "power_off"
                                    connect_btn = (
                                        ui.button(icon=icon_name, on_click=self._create_connect_handler(i))
                                        .props("unelevated")
                                        .classes(f"{btn_color} w-16 h-8 rounded shadow")
                                    )
                                    self._route_buttons[i] = connect_btn
                                    ui.button(icon="delete", on_click=self._create_route_delete_handler(i)).props(
                                        "unelevated"
                                    ).classes("bg-red-300 hover:bg-red-400 text-red-900 w-16 h-8 rounded shadow")

        except Exception:
            self._logger.exception("Error refreshing route table")

    def _update_route_button(self) -> None:
        """Update route button state."""
        if self.add_route_btn:
            has_remote = any(h["remote"] for h in self._hosts)
            if has_remote:
                self.add_route_btn.props(remove="disable")
                self.add_route_btn.classes(replace="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded")
            else:
                self.add_route_btn.props(add="disable")
                self.add_route_btn.classes(replace="bg-gray-100 text-gray-400 cursor-not-allowed px-6 py-2 rounded")

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

    def move_host(self, from_index: int, to_index: int) -> None:
        """Move host from one position to another."""
        if 0 <= from_index < len(self._hosts) and 0 <= to_index < len(self._hosts):
            host = self._hosts.pop(from_index)
            self._hosts.insert(to_index, host)
            self._selected_host = None  # Clear selection after move
            self._save_to_file()
            self._refresh_table()

    def move_route(self, from_index: int, to_index: int) -> None:
        """Move route from one position to another."""
        if 0 <= from_index < len(self._routes) and 0 <= to_index < len(self._routes):
            route = self._routes.pop(from_index)
            self._routes.insert(to_index, route)
            self._selected_route = None  # Clear selection after move
            # Update connected routes indices
            new_connected = set()
            for conn_idx in self._connected_routes:
                if conn_idx == from_index:
                    new_connected.add(to_index)
                elif from_index < to_index and conn_idx > from_index and conn_idx <= to_index:
                    new_connected.add(conn_idx - 1)
                elif from_index > to_index and conn_idx >= to_index and conn_idx < from_index:
                    new_connected.add(conn_idx + 1)
                else:
                    new_connected.add(conn_idx)
            self._connected_routes = new_connected
            self._save_to_file()
            self._refresh_route_table()

    def _connect_route(self, index: int) -> None:
        """Connect/disconnect route."""
        try:
            if 0 <= index < len(self._routes):
                route = self._routes[index]

                if index in self._connected_routes:
                    # Disconnect
                    self._connected_routes.discard(index)
                    ui.notify(f"Disconnected from {route['summary']}", color="warning")
                    self._update_connection_status()
                else:
                    # Connect
                    ui.notify(f"Connecting to {route['summary']}...", color="info")
                    try:
                        # Simulate connection (replace with actual SSH logic)
                        self._connected_routes.add(index)
                        ui.notify("Connection successful!", color="positive")
                        self._update_connection_status()
                        if self._on_connection_success:
                            self._on_connection_success()
                    except Exception:
                        self._logger.exception("SSH connection failed")
                        ui.notify("Connection failed", color="negative")

                self._refresh_route_table()
        except Exception:
            self._logger.exception("Error connecting to route")
            ui.notify("Connection failed", color="negative")

    def _update_connection_status(self) -> None:
        """Update host tab icon color based on connection status."""
        if self._connected_routes:
            # Green if any connections
            if self._on_connection_success:
                self._on_connection_success()
        # Red if no connections
        elif hasattr(self, "_on_connection_failure") and self._on_connection_failure:
            self._on_connection_failure()

    def _save_config(self) -> None:
        """Save configuration to ~/.interface-check/ssh_config.json for debug."""
        try:
            config_dir = Path.home() / ".interface-check"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "ssh_config.json"

            config = {"hosts": self._hosts, "routes": self._routes}
            with config_path.open("w") as f:
                json.dump(config, f, indent=2)

            ui.notify(f"Configuration saved to {config_path}", color="positive")
        except Exception:
            self._logger.exception("Error saving config")
            ui.notify("Failed to save configuration", color="negative")

    def _export_config(self) -> None:
        """Export configuration to JSON."""
        try:
            config = {"hosts": self._hosts, "routes": self._routes}
            config_json = json.dumps(config, indent=2)
            ui.download(config_json.encode(), "ssh_config.json")
            ui.notify("Configuration exported successfully", color="positive")
        except Exception:
            self._logger.exception("Error exporting config")
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
            self._logger.exception("Error reading file")

    def _import_config(self, config_text: str, dialog: ui.dialog) -> None:
        """Import configuration from JSON."""
        try:
            if not config_text or not config_text.strip():
                ui.notify("Please provide configuration JSON", color="negative")
                return

            config = json.loads(config_text.strip())
            if not isinstance(config, dict) or "hosts" not in config:
                ui.notify("Invalid configuration format", color="negative")
                return

            hosts = config.get("hosts", [])
            routes = config.get("routes", [])

            self._hosts = hosts
            self._routes = routes if isinstance(routes, list) else []
            self._remote_index = None

            # Reset all host selections
            for host in self._hosts:
                host["remote"] = False
                host["jump"] = False
                host["jump_order"] = None

            # Reset table states
            self.hosts_expanded = True
            self.routes_expanded = True

            # Update toggle button icons
            if self.hosts_toggle_btn:
                self.hosts_toggle_btn.props("icon=expand_less")
            if self.routes_toggle_btn:
                self.routes_toggle_btn.props("icon=expand_less")

            dialog.close()
            self._refresh_table()
            self._refresh_route_table()
            ui.notify(f"Imported {len(hosts)} hosts and {len(self._routes)} routes", color="positive")

        except json.JSONDecodeError:
            ui.notify("Invalid JSON format", color="negative")
        except Exception:
            self._logger.exception("Error importing config")

    def _select_host_for_move(self, index: int) -> None:
        """Select host for moving."""
        if self._selected_host is None:
            self._selected_host = index
            ui.notify(f"Host {index + 1} selected. Click another host to move.", color="info")
            self._refresh_table()
        else:
            if self._selected_host != index:
                self.move_host(self._selected_host, index)
                ui.notify(f"Moved host {self._selected_host + 1} to position {index + 1}", color="positive")
            self._selected_host = None
            self._refresh_table()

    def _select_route_for_move(self, index: int) -> None:
        """Select route for moving."""
        if self._selected_route is None:
            self._selected_route = index
            ui.notify(f"Route {index + 1} selected. Click another route to move.", color="info")
            self._refresh_route_table()
        else:
            if self._selected_route != index:
                self.move_route(self._selected_route, index)
                ui.notify(f"Moved route {self._selected_route + 1} to position {index + 1}", color="positive")
            self._selected_route = None
            self._refresh_route_table()

    def _cancel_host_move_if_outside_drag(self, event: Any, _index: int) -> None:
        """Cancel host move if clicking outside drag indicator."""
        # Check if click target is the drag indicator
        if hasattr(event, "target") and "drag_indicator" not in str(event.target) and self._selected_host is not None:
            self._selected_host = None
            ui.notify("Move operation canceled", color="warning")
            self._refresh_table()

    def _cancel_route_move_if_outside_drag(self, event: Any, _index: int) -> None:
        """Cancel route move if clicking outside drag indicator."""
        # Check if click target is the drag indicator
        if hasattr(event, "target") and "drag_indicator" not in str(event.target) and self._selected_route is not None:
            self._selected_route = None
            ui.notify("Move operation canceled", color="warning")
            self._refresh_route_table()
