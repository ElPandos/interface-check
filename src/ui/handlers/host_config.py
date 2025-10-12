"""Host configuration management."""

import logging
from typing import Any

from src.models.configurations import AppConfig, Host
from src.utils.configure import Configure

logger = logging.getLogger(__name__)


class HostConfigManager:
    """Manages host and route configuration."""

    def __init__(self) -> None:
        self.hosts: list[dict[str, Any]] = []
        self.routes: list[dict[str, Any]] = []
        self.remote_index: int | None = None

    def load(self) -> None:
        """Load configuration from file."""
        try:
            app_config = Configure().load()
            self.hosts = [
                {
                    "summary": host.summary,
                    "ip": host.ip,
                    "username": host.username,
                    "password": host.password.get_secret_value(),
                    "remote": host.remote,
                    "jump": host.jump,
                    "jump_order": host.jump_order,
                }
                for host in app_config.hosts
            ]
            self.routes = app_config.routes
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
                    summary=host.get("summary"),
                    ip=host["ip"],
                    username=host["username"],
                    password=host["password"],
                    remote=host["remote"],
                    jump=host["jump"],
                    jump_order=host.get("jump_order"),
                )
                for host in self.hosts
            ]

            app_config = Configure().load()
            app_config.hosts = hosts
            app_config.routes = self.routes
            Configure().save(app_config)
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
            host["remote"] = False
            host["jump"] = False
            host["jump_order"] = None
        self.remote_index = None

    def add_host(self, host_data: dict[str, Any]) -> None:
        """Add new host."""
        self.hosts.append(host_data)
        self._reset_host_states()

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

    def get_available_jump_orders(self, current_host: dict) -> list[str]:
        """Get available jump orders for host."""
        used_orders = {h["jump_order"] for h in self.hosts if h["jump_order"] and h != current_host}
        return [str(j) for j in range(1, len(self.hosts)) if j not in used_orders]
