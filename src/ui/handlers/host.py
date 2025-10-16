"""Host connection manager for centralized SSH management."""

from collections.abc import Callable
import logging
from typing import Any

from nicegui import ui

from src.core.connect import SshConnection
from src.models.config import Config

logger = logging.getLogger(__name__)


class HostHandler:
    """Manages SSH connections and host selection across all tabs."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._current_host_index: int | None = None
        self._connection_callbacks: list[Callable[[SshConnection | None], None]] = []
        self._host_selectors: list[ui.select] = []
        self._route_connections: dict[int, SshConnection] = {}

    @property
    def current_connection(self) -> SshConnection | None:
        """Get current SSH connection."""
        return getattr(self, "_current_connection", None)

    @property
    def current_host_index(self) -> int | None:
        """Get current host index."""
        return self._current_host_index

    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._current_connection is not None and self._current_connection.is_connected()

    def register_connection_callback(self, callback: Callable[[SshConnection | None], None]) -> None:
        """Register callback for connection changes."""
        self._connection_callbacks.append(callback)

    def register_host_selector(self, selector: ui.select) -> None:
        """Register host selector for synchronization."""
        self._host_selectors.append(selector)

    def get_host_options(self) -> list[dict[str, Any]]:
        """Get host options for selectors."""
        if not self._config.networks.hosts:
            return [{"label": "No hosts configured", "value": None}]

        return [
            {"label": f"{host.ip} ({host.username})", "value": i} for i, host in enumerate(self._config.networks.hosts)
        ]

    def connect_to_host(self, host_index: int | None) -> bool:
        """Connect to specified host."""
        if host_index is None:
            self.disconnect()
            return True

        if not (0 <= host_index < len(self._config.networks.hosts)):
            logger.error("Invalid host index: %s", host_index)
            return False

        host = self._config.networks.hosts[host_index]

        try:
            # Disconnect existing connection
            if hasattr(self, "_current_connection") and self._current_connection:
                self._current_connection.disconnect()

            # Create new connection
            self._current_connection = SshConnection(
                host=host.ip, username=host.username, password=host.password.get_secret_value()
            )

            if self._current_connection.connect():
                self._current_host_index = host_index
                self._update_selectors(host_index)
                self._notify_callbacks()
                ui.notify(f"Connected to {host.ip}", color="positive")
                logger.info("Connected to host %s", host.ip)
                return True
            self._current_connection = None
            ui.notify(f"Failed to connect to {host.ip}", color="negative")
            logger.error("Failed to connect to host %s", host.ip)
            return False

        except Exception as e:
            self._current_connection = None
            ui.notify(f"Connection error: {e}", color="negative")
            logger.exception("Connection error for host %s", host.ip)
            return False

    def disconnect(self) -> None:
        """Disconnect current connection."""
        if hasattr(self, "_current_connection") and self._current_connection:
            try:
                self._current_connection.disconnect()
                ui.notify("Disconnected", color="warning")
                logger.info("Disconnected from host")
            except Exception:
                logger.exception("Error during disconnect")

        self._current_connection = None
        self._current_host_index = None
        self._update_selectors(None)
        self._notify_callbacks()

    def _update_selectors(self, host_index: int | None) -> None:
        """Update all registered host selectors."""
        for selector in self._host_selectors:
            if selector:
                selector.value = host_index

    def _notify_callbacks(self) -> None:
        """Notify all registered callbacks of connection change."""
        for callback in self._connection_callbacks:
            try:
                callback(self._current_connection)
            except Exception:
                logger.exception("Error in connection callback")

    def create_host_selector(self, on_change: Callable[[int | None], None] | None = None) -> ui.select:
        """Create a synchronized host selector."""
        selector = ui.select(
            options=self.get_host_options(),
            value=self._current_host_index,
            on_change=lambda e: self._handle_selector_change(e.value, on_change),
        ).classes("min-w-48")

        self.register_host_selector(selector)
        return selector

    def _handle_selector_change(self, host_index: int | None, callback: Callable[[int | None], None] | None) -> None:
        """Handle host selector change."""
        if host_index != self._current_host_index:
            if host_index is None:
                self.disconnect()
            else:
                self.connect_to_host(host_index)

        if callback:
            callback(host_index)

    def refresh_host_options(self) -> None:
        """Refresh host options in all selectors."""
        options = self.get_host_options()
        for selector in self._host_selectors:
            if selector:
                selector.options = options

    def connect_to_route(self, route_index: int) -> bool:
        """Connect to a specific route."""
        if not self._config.networks.routes:
            logger.error("No routes configured")
            ui.notify("No routes configured", color="negative")
            return False
            
        if route_index < 0 or route_index >= len(self._config.networks.routes):
            logger.error("Invalid route index: %s (max: %s)", route_index + 1, len(self._config.networks.routes))
            ui.notify(f"Invalid route index: {route_index}", color="negative")
            return False

        route = self._config.networks.routes[route_index]

        try:
            connection = SshConnection.from_route(route)
            if connection.connect():
                self._route_connections[route_index] = connection
                ui.notify(f"Connected to route: {route.summary}", color="positive")
                logger.info("Connected to route %s: %s", route_index + 1, route.summary)
                return True
            ui.notify(f"Failed to connect to route: {route.summary}", color="negative")
            logger.error("Failed to connect to route %s: %s", route_index + 1, route.summary)
            return False
        except Exception as e:
            ui.notify(f"Connection error: {e}", color="negative")
            logger.exception("Connection error for route %s: %s", route_index + 1, route.summary)
            return False

    def disconnect_from_route(self, route_index: int) -> None:
        """Disconnect from a specific route."""
        if route_index in self._route_connections:
            try:
                self._route_connections[route_index].disconnect()
                del self._route_connections[route_index]
                ui.notify("Disconnected from route", color="warning")
                logger.info("Disconnected from route %s", route_index + 1)
            except Exception:
                logger.exception("Error disconnecting from route")

    def is_route_connected(self, route_index: int) -> bool:
        """Check if a route is connected."""
        connection = self._route_connections.get(route_index)
        return connection is not None and connection.is_connected()

    def get_route_connection(self, route_index: int) -> SshConnection | None:
        """Get connection for a specific route."""
        return self._route_connections.get(route_index)
