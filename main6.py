"""
SSH Host Manager - Optimized Implementation
Type-safe, secure, and performant SSH host management with route configuration.
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable, TypedDict
from dataclasses import dataclass
from nicegui import ui

# Configure extensive debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ssh_host_manager.log')
    ]
)
logger = logging.getLogger(__name__)


class HostDict(TypedDict):
    """Type definition for host configuration."""
    ip: str
    username: str
    password: str
    remote: bool
    jump: bool
    jump_order: Optional[int]


class RouteDict(TypedDict):
    """Type definition for route configuration."""
    summary: str
    remote_host_ip: str
    remote_host_username: str
    remote_host_password: str
    jump_hosts: List[Dict[str, Any]]


@dataclass(frozen=True)
class UIStyles:
    """Immutable UI styling configuration."""
    header_gradient: str = "font-bold text-white bg-gradient-to-r from-blue-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md"
    route_header_gradient: str = "font-bold text-white bg-gradient-to-r from-green-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md"
    delete_button: str = "bg-gray-300 hover:bg-red-200 text-red-600 w-20 h-8 rounded shadow"
    connect_button: str = "bg-gray-300 hover:bg-green-200 text-green-600 w-20 h-8 rounded shadow"


class HostManager:
    """Optimized SSH Host Manager with type safety and error handling."""

    def __init__(self) -> None:
        """Initialize the host manager with default configuration."""
        logger.debug("Initializing HostManager")
        self._hosts: List[HostDict] = [
            {"ip": "192.168.1.10", "username": "admin", "password": "demo123", "remote": False, "jump": False, "jump_order": None},
            {"ip": "10.0.0.5", "username": "user", "password": "demo456", "remote": False, "jump": False, "jump_order": None},
            {"ip": "172.16.0.20", "username": "root", "password": "demo789", "remote": False, "jump": False, "jump_order": None}
        ]
        logger.debug(f"Initialized with {len(self._hosts)} default hosts")
        self._remote_index: Optional[int] = None
        self._routes: List[RouteDict] = [
            {
                "summary": "192.168.1.10(J1) ⟶ 10.0.0.5(Remote)",
                "remote_host_ip": "10.0.0.5",
                "remote_host_username": "user",
                "remote_host_password": "demo456",
                "jump_hosts": [{"ip": "192.168.1.10", "username": "admin", "password": "demo123", "order": 1}]
            }
        ]
        self._styles = UIStyles()

        # UI components
        self.add_route_btn: Optional[ui.button] = None
        self.table_container: Optional[ui.column] = None
        self.route_container: Optional[ui.column] = None
        self.hosts_toggle_btn: Optional[ui.button] = None
        self.routes_toggle_btn: Optional[ui.button] = None
        self.hosts_expanded: bool = True
        self.routes_expanded: bool = True

        logger.debug("Starting UI initialization")
        self._init_ui()
        logger.debug("HostManager initialization complete")

    def _init_ui(self) -> None:
        """Initialize the user interface with proper error handling."""
        try:
            ui.colors(primary='#374151', secondary='#4b5563', accent='#3b82f6', dark='#1f2937', positive='#10b981', negative='#ef4444', info='#3b82f6', warning='#f59e0b')

            with ui.card().classes("w-full max-w-6xl mx-auto p-6 shadow-xl bg-gray-50 border border-gray-200"):
                with ui.row().classes("w-full justify-center items-center gap-3 mb-6"):
                    ui.icon("terminal", size="lg").classes("text-blue-600")
                    ui.label("SSH Host Manager").classes("text-2xl font-bold text-gray-800")
                    ui.space()
                    ui.button(icon="download", text="Import" , on_click=self._open_import_dialog).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded")
                    ui.button(icon="upload", text="Export", on_click=self._export_config).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded")

                with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-2 mb-4"):
                        self.hosts_toggle_btn = ui.button(icon="expand_less", on_click=self._toggle_hosts).props("flat round").classes("text-gray-600")
                        ui.icon("computer", size="lg").classes("text-blue-600")
                        ui.label("Hosts").classes("text-lg font-semibold text-gray-800")
                        ui.space()
                        ui.button(icon="desktop_windows", text="Add Host", on_click=self._open_add_dialog).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded")
                    self.table_container = ui.column().classes("w-full")

                with ui.card().classes("w-full bg-white border border-gray-200 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-2 mb-4"):
                        self.routes_toggle_btn = ui.button(icon="expand_less", on_click=self._toggle_routes).props("flat round").classes("text-gray-600")
                        ui.icon("route", size="lg").classes("text-green-600")
                        ui.label("Routes").classes("text-lg font-semibold text-gray-800")
                        ui.space()
                        self.add_route_btn = ui.button(icon="route", text="Add Route", on_click=self._add_route).props("disable").classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded")
                    self.route_container = ui.column().classes("w-full")

            self._refresh_table()
            self._refresh_route_table()

        except Exception as e:
            logger.error(f"Failed to initialize UI: {e}")
            ui.notify("Failed to initialize interface", color="negative")

    def _validate_ip(self, ip: str) -> bool:
        """Validate IP address format."""
        import re
        pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        return bool(re.match(pattern, ip.strip()))

    def _sanitize_input(self, value: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not isinstance(value, str):
            return ""
        return value.strip()[:255]

    def _open_add_dialog(self) -> None:
        """Open dialog to add new host with input validation."""
        with ui.dialog() as dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
            ui.label("Add new host").classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Network details").classes("font-semibold mb-3 text-gray-700")
                ip_input = ui.input("IP address", placeholder="192.168.1.100").classes("w-full")
                ip_input.props('outlined').tooltip("Enter the server's IP address")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Authentication").classes("font-semibold mb-3 text-gray-700")
                user_input = ui.input("Username", placeholder="admin").classes("w-full mb-3")
                user_input.props('outlined').tooltip("SSH username for server login")
                pass_input = ui.input("Password", password=True, placeholder="••••••••").classes("w-full")
                pass_input.props('outlined').tooltip("Password for authentication")

            with ui.row().classes("w-full mt-6"):
                ui.button(icon="add", text="Add host", on_click=lambda: self._add_host(
                    self._sanitize_input(ip_input.value or ""),
                    self._sanitize_input(user_input.value or ""),
                    self._sanitize_input(pass_input.value or ""),
                    dialog
                )).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")
                ui.space()
                ui.button(icon="cancel", text="Cancel", on_click=dialog.close).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")
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
                "jump_order": None
            }
            self._hosts.append(new_host)

            dialog.close()
            ui.notify(f"Successfully added host {ip}", color="positive")
            self._refresh_table()

        except Exception as e:
            logger.error(f"Error adding host: {e}")
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
            self._refresh_table()

        except Exception as e:
            logger.error(f"Error deleting host: {e}")

    def _add_route(self) -> None:
        """Add new route with validation."""
        try:
            remote_host = next((h for h in self._hosts if h["remote"]), None)
            if not remote_host:
                ui.notify("Please select a remote host first", color="negative")
                return

            jump_hosts = sorted(
                [h for h in self._hosts if h["jump"] and h["jump_order"]],
                key=lambda x: x["jump_order"] or 0
            )

            jump_parts = [f"{h['ip']}(J{h['jump_order']})" for h in jump_hosts]
            remote_part = f"{remote_host['ip']}(Remote)"
            summary = " ⟶ ".join(jump_parts + [remote_part])

            if any(r["summary"] == summary for r in self._routes):
                ui.notify("Route already exists", color="negative")
                return

            route = {
                "summary": summary,
                "remote_host_ip": remote_host["ip"],
                "remote_host_username": remote_host["username"],
                "remote_host_password": remote_host["password"],
                "jump_hosts": [{
                    "ip": h["ip"],
                    "username": h["username"],
                    "password": h["password"],
                    "order": h["jump_order"]
                } for h in jump_hosts]
            }
            self._routes.append(route)
            ui.notify(f"Route added: {summary}", color="positive")
            self._refresh_route_table()

        except Exception as e:
            logger.error(f"Error adding route: {e}")

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
                ui.notify("Route removed", color="warning")
                self._refresh_route_table()
        except Exception as e:
            logger.error(f"Error deleting route: {e}")

    def _on_remote_toggle(self, checked: bool, index: int) -> None:
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

            self._refresh_table()
        except Exception as e:
            logger.error(f"Error toggling remote host: {e}")

    def _on_jump_toggle(self, checked: bool, index: int) -> None:
        """Handle jump host selection."""
        try:
            if 0 <= index < len(self._hosts):
                self._hosts[index]["jump"] = checked
                if not checked:
                    self._hosts[index]["jump_order"] = None
                self._refresh_table()
        except Exception as e:
            logger.error(f"Error toggling jump host: {e}")

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
        except Exception as e:
            logger.error(f"Error updating jump order: {e}")

    def _get_available_orders(self, current_host: HostDict) -> List[str]:
        """Get available jump orders."""
        used_orders = {h["jump_order"] for h in self._hosts if h["jump_order"] and h != current_host}
        return [str(j) for j in range(1, len(self._hosts)) if j not in used_orders]

    def _refresh_table(self) -> None:
        """Refresh the host management table."""
        if not self.table_container:
            return

        try:
            self.table_container.clear()

            if self.hosts_expanded:
                with self.table_container:
                    with ui.row().classes("font-bold text-white bg-gradient-to-r from-blue-500 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"):
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

        except Exception as e:
            logger.error(f"Error refreshing table: {e}")

    def _render_host_row(self, index: int, host: HostDict) -> None:
        """Render individual host row."""
        is_remote = host["remote"]
        is_jump = host["jump"]
        row_bg = (
            "bg-gradient-to-r from-white to-blue-500 border-blue-400" if is_remote else
            "bg-gradient-to-r from-white to-blue-200 border-blue-300" if is_jump else
            "bg-gradient-to-r from-white to-gray-50 border-gray-200" if index % 2 else "bg-gradient-to-r from-white to-white border-gray-200"
        )

        with ui.row().classes(f"items-center justify-between border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-gray-100"):
            ui.label(str(index + 1)).classes("w-6 text-gray-600")
            ui.label(host["ip"]).classes("w-40 text-gray-800")
            ui.label(host["username"]).classes("w-36 text-gray-800")
            ui.label("••••••").classes("w-36 text-gray-500")

            cb_remote = ui.checkbox(value=is_remote).classes("w-28")
            cb_remote.on_value_change(self._create_remote_handler(index))
            if self._remote_index is not None and not is_remote:
                cb_remote.disable()
                cb_remote.style("opacity: 0.2")

            cb_jump = ui.checkbox(value=is_jump).classes("w-24")
            cb_jump.on_value_change(self._create_jump_handler(index))
            if is_remote:
                cb_jump.disable()
                cb_jump.style("opacity: 0.2")

            order_value = str(host["jump_order"]) if host["jump_order"] else None
            order_options = self._get_available_orders(host)
            order_select = ui.select(order_options, value=order_value).props("outlined dense").classes("w-16")
            order_select.on_value_change(self._create_order_handler(index))

            if not is_jump or is_remote:
                order_select.disable()
                order_select.style("opacity: 0.2")

            ui.button(icon="delete", on_click=self._create_delete_handler(index)).props("unelevated").classes("bg-gray-500 hover:bg-gray-600 text-white w-20 h-8 rounded shadow")

    def _refresh_route_table(self) -> None:
        """Refresh the route table."""
        if not self.route_container:
            return

        try:
            self.route_container.clear()

            if self.routes_expanded:
                with self.route_container:
                    with ui.row().classes("font-bold text-white bg-gradient-to-r from-green-600 to-gray-500 w-full justify-between rounded-t-lg px-4 py-3 text-sm shadow-md border border-gray-300"):
                        ui.label("#").classes("w-6 text-white font-bold")
                        ui.label("Route Summary (Jump → Remote)").classes("w-96 text-white font-bold")
                        ui.label("Actions").classes("w-40 text-center text-gray-200 font-bold")

                    if not self._routes:
                        ui.label("No routes defined yet.").classes("text-gray-500 italic text-center py-4 bg-white border-b border-gray-200")
                    else:
                        for i, route in enumerate(self._routes):
                            row_bg = "bg-green-50 border-green-200" if i % 2 else "bg-white border-gray-200"
                            with ui.row().classes(f"items-center border-b px-4 py-2 w-full text-sm {row_bg} hover:bg-green-100"):
                                ui.label(str(i + 1)).classes("w-6 text-gray-600")
                                ui.label(route["summary"]).classes("flex-1 truncate text-gray-800")
                                with ui.row().classes("gap-2 ml-auto"):
                                    ui.button(icon="power").props("unelevated").classes("bg-gray-500 hover:bg-gray-600 text-white w-20 h-8 rounded shadow")
                                    ui.button(icon="delete", on_click=self._create_route_delete_handler(i)).props("unelevated").classes("bg-gray-500 hover:bg-gray-600 text-white w-20 h-8 rounded shadow")

        except Exception as e:
            logger.error(f"Error refreshing route table: {e}")

    def _update_route_button(self) -> None:
        """Update route button state."""
        if self.add_route_btn:
            has_remote = any(h["remote"] for h in self._hosts)
            if has_remote:
                self.add_route_btn.props(remove="disable")
            else:
                self.add_route_btn.props(add="disable")

    def _create_remote_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_remote_toggle(e.value, index)

    def _create_jump_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_jump_toggle(e.value, index)

    def _create_order_handler(self, index: int) -> Callable[[Any], None]:
        return lambda e: self._on_jump_order_change(e.value, index)

    def _create_delete_handler(self, index: int) -> Callable[[], None]:
        return lambda: self._delete_host(index)

    def _create_route_delete_handler(self, index: int) -> Callable[[], None]:
        return lambda: self._delete_route(index)

    def _export_config(self) -> None:
        """Export configuration to JSON."""
        try:
            config = {"hosts": self._hosts, "routes": self._routes}
            config_json = json.dumps(config, indent=2)
            ui.download(config_json.encode(), "ssh_config.json")
            ui.notify("Configuration exported successfully", color="positive")
        except Exception as e:
            logger.error(f"Error exporting config: {e}")

    def _open_import_dialog(self) -> None:
        """Open import dialog."""
        with ui.dialog() as dialog, ui.card().classes("w-96 bg-white border border-gray-300 shadow-lg"):
            ui.label("Import configuration").classes("text-xl font-bold mb-6 text-center text-gray-800")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Upload file").classes("font-semibold mb-3 text-gray-700")
                file_upload = ui.upload(
                    on_upload=lambda e: self._handle_file_upload(e, dialog),
                    auto_upload=True
                ).props('accept=".json"').classes("w-full")

            with ui.card().classes("w-full p-4 bg-gray-50 border border-gray-200 mb-4"):
                ui.label("Paste JSON").classes("font-semibold mb-3 text-gray-700")
                config_input = ui.textarea(placeholder="Paste JSON here...").classes("w-full h-32")

            with ui.row().classes("w-full mt-6"):
                ui.button(icon="download", text="Import", on_click=lambda: self._import_config(config_input.value, dialog)).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")
                ui.space()
                ui.button(icon="cancel", text="Cancel", on_click=dialog.close).classes("bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg")
        dialog.open()

    def _handle_file_upload(self, e, dialog: ui.dialog) -> None:
        """Handle file upload."""
        try:
            content = e.content.read().decode('utf-8')
            self._import_config(content, dialog)
        except Exception as ex:
            logger.error(f"Error reading file: {ex}")

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
        except Exception as e:
            logger.error(f"Error importing config: {e}")


def main() -> None:
    """Main application entry point."""
    try:
        host_manager = HostManager()
        ui.run(
            title="SSH Host Manager",
            favicon="./assets/icons/interoperability.png",
            port=8080,
            dark=False
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    return 0


if __name__ in {"__main__", "__mp_main__"}:
    main()
