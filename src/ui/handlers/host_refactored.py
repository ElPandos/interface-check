"""Refactored SSH Host Manager using new base classes."""

import logging
from typing import Any

from nicegui import ui

from src.core import AppConfigManager, HostValidator, Result, sanitize_input
from src.core.connection import ConnectionConfig, SshConnection
from src.ui.base import FormWidget, TableWidget, Widget

logger = logging.getLogger(__name__)


class HostFormWidget(FormWidget):
    """Host configuration form widget."""

    def __init__(self):
        super().__init__("host_form", "Add New Host")
        self._validator = HostValidator()

    def _build_form(self) -> None:
        """Build host form fields."""
        self.add_field(
            "ip",
            "input",
            "IP Address",
            validator=lambda x: self._validator.validate({"ip": x, "username": "test", "password": "test"}),
            placeholder="192.168.1.100",
        )

        self.add_field("username", "input", "Username", placeholder="admin")

        self.add_field("password", "input", "Password", password=True, placeholder="••••••••")

        with ui.row().classes("w-full mt-4"):
            ui.button("Add Host", on_click=self._on_add_host).classes("bg-blue-500 text-white")
            ui.button("Cancel", on_click=self._on_cancel).classes("bg-gray-300 text-gray-800 ml-2")

    def _on_add_host(self) -> None:
        """Handle add host button click."""
        result = self.validate()
        if result.success:
            self.trigger_event("host_added", result.data)
            self.clear()
        else:
            ui.notify(f"Validation failed: {result.error}", color="negative")

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.clear()
        self.trigger_event("form_cancelled")


class HostTableWidget(TableWidget):
    """Host management table widget."""

    def __init__(self):
        columns = ["#", "IP Address", "Username", "Status", "Actions"]
        super().__init__("host_table", "SSH Hosts", columns)
        self.selectable = True
        self._connections: dict[str, SshConnection] = {}

    def add_host(self, host_data: dict[str, Any]) -> None:
        """Add host to table."""
        index = len(self.rows)
        row = {
            "#": str(index + 1),
            "IP Address": host_data["ip"],
            "Username": host_data["username"],
            "Status": "Disconnected",
            "Actions": "Connect",
            "host_data": host_data,
            "index": index,
        }
        self.add_row(row)

    def connect_host(self, index: int) -> Result[None]:
        """Connect to host."""
        if index >= len(self.rows):
            return Result.fail("Invalid host index")

        host_data = self.rows[index]["host_data"]
        config = ConnectionConfig(host=host_data["ip"], username=host_data["username"], password=host_data["password"])

        connection = SshConnection(config)
        result = connection.connect()

        if result.success:
            self._connections[host_data["ip"]] = connection
            self.rows[index]["Status"] = "Connected"
            self.rows[index]["Actions"] = "Disconnect"
            self._update_table_data()
            return Result.ok(None)
        return result

    def disconnect_host(self, index: int) -> None:
        """Disconnect from host."""
        if index >= len(self.rows):
            return

        host_data = self.rows[index]["host_data"]
        if host_data["ip"] in self._connections:
            self._connections[host_data["ip"]].disconnect()
            del self._connections[host_data["ip"]]
            self.rows[index]["Status"] = "Disconnected"
            self.rows[index]["Actions"] = "Connect"
            self._update_table_data()


class HostManagerWidget(Widget):
    """Main host manager widget."""

    def __init__(self):
        super().__init__("host_manager", "SSH Host Manager")
        self._config_manager = AppConfigManager()
        self._host_form: HostFormWidget | None = None
        self._host_table: HostTableWidget | None = None
        self._form_dialog: ui.dialog | None = None

    def _do_initialize(self) -> None:
        """Initialize host manager."""
        result = self._config_manager.initialize()
        if not result.success:
            logger.error(f"Failed to initialize config manager: {result.error}")

        result = self._config_manager.load_or_create_default()
        if not result.success:
            logger.error(f"Failed to load config: {result.error}")

        super()._do_initialize()

    def _build_ui(self) -> None:
        """Build host manager UI."""
        self._container = ui.column().classes("w-full h-screen p-4")

        with self._container:
            # Header
            with ui.card().classes("w-full p-6 mb-4"), ui.row().classes("w-full items-center"):
                ui.icon("computer", size="lg").classes("text-blue-600")
                ui.label("SSH Host Manager").classes("text-2xl font-bold ml-2")
                ui.space()
                ui.button("Add Host", icon="add", on_click=self._show_add_form).classes("bg-blue-500 text-white")
                ui.button("Save Config", icon="save", on_click=self._save_config).classes(
                    "bg-green-500 text-white ml-2"
                )

            # Host table
            self._host_table = HostTableWidget()
            self._host_table.initialize()
            self._host_table.add_event_handler("selection_changed", self._on_host_selection_changed)

            # Load existing hosts
            self._load_hosts()

    def _show_add_form(self) -> None:
        """Show add host form dialog."""
        self._form_dialog = ui.dialog()

        with self._form_dialog, ui.card().classes("w-96"):
            self._host_form = HostFormWidget()
            self._host_form.initialize()
            self._host_form.add_event_handler("host_added", self._on_host_added)
            self._host_form.add_event_handler("form_cancelled", self._on_form_cancelled)

        self._form_dialog.open()

    def _on_host_added(self, host_data: dict[str, Any]) -> None:
        """Handle host added event."""
        # Sanitize input
        sanitized_data = {
            "ip": sanitize_input(host_data["ip"]),
            "username": sanitize_input(host_data["username"]),
            "password": sanitize_input(host_data["password"]),
        }

        # Add to table
        self._host_table.add_host(sanitized_data)

        # Save to config
        hosts = self._config_manager.get_hosts()
        hosts.append(sanitized_data)
        self._config_manager.set("hosts", hosts)

        ui.notify(f"Host {sanitized_data['ip']} added successfully", color="positive")
        self._form_dialog.close()

    def _on_form_cancelled(self) -> None:
        """Handle form cancelled event."""
        self._form_dialog.close()

    def _on_host_selection_changed(self, selected_indices: list[int]) -> None:
        """Handle host selection change."""
        if selected_indices:
            logger.info(f"Selected hosts: {selected_indices}")

    def _load_hosts(self) -> None:
        """Load hosts from configuration."""
        hosts = self._config_manager.get_hosts()
        for host in hosts:
            self._host_table.add_host(host)

    def _save_config(self) -> None:
        """Save configuration."""
        result = self._config_manager.save(self._config_manager.data)
        if result.success:
            ui.notify("Configuration saved", color="positive")
        else:
            ui.notify(f"Failed to save: {result.error}", color="negative")


class RefactoredHostHandler:
    """Refactored host handler using new architecture."""

    def __init__(self):
        self._widget: HostManagerWidget | None = None

    def build(self) -> None:
        """Build host manager interface."""
        self._widget = HostManagerWidget()
        result = self._widget.initialize()

        if not result.success:
            logger.error(f"Failed to initialize host manager: {result.error}")
            ui.notify("Failed to initialize host manager", color="negative")

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._widget:
            self._widget.cleanup()
