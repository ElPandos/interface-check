"""Route connection management."""

import logging
from typing import Any

from nicegui import ui

from src.models.configurations import AppConfig, Host
from src.utils.connect import Ssh

logger = logging.getLogger(__name__)


class RouteConnectionManager:
    """Manages route connections and states."""

    def __init__(self) -> None:
        self._connected_routes: dict[int, Ssh] = {}
        self._route_buttons: dict[int, ui.button] = {}

    def is_connected(self, route_index: int) -> bool:
        """Check if route is connected."""
        return route_index in self._connected_routes and self._connected_routes[route_index].is_connected()

    def connect_route(self, route_index: int, route_data: dict[str, Any]) -> bool:
        """Connect to route. Returns True if successful."""
        try:
            summary = self._get_route_summary(route_data)
            ui.notify(f"Connecting to {summary}...", color="info")

            ssh = Ssh(AppConfig(hosts=route_data["hosts"]))
            ssh.initialize()

            if ssh.is_connected():
                self._connected_routes[route_index] = ssh
                ui.notify("Connection successful!", color="positive")
                return True

            ui.notify("Connection failed!", color="warning")
            return False

        except Exception:
            logger.exception("SSH connection failed")
            ui.notify("Connection failed", color="negative")
            return False

    def disconnect_route(self, route_index: int, route_data: dict[str, Any]) -> None:
        """Disconnect from route."""
        if route_index in self._connected_routes:
            self._connected_routes[route_index].cleanup()
            del self._connected_routes[route_index]
        self._connected_routes.discard(route_index)
        summary = self._get_route_summary(route_data)
        ui.notify(f"Disconnected from {summary}", color="warning")

    def update_connected_indices_after_move(self, from_index: int, to_index: int) -> None:
        """Update connected route indices after a move operation."""
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

    def create_route_from_hosts(self, hosts: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Create route from selected hosts."""
        remote_host = next((h for h in hosts if h["remote"]), None)
        if not remote_host:
            return None

        jump_hosts = sorted([h for h in hosts if h["jump"] and h["jump_order"]], key=lambda x: x["jump_order"] or 0)

        jump_parts = [f"{h['ip']}(J{h['jump_order']})" for h in jump_hosts]
        remote_part = f"{remote_host['ip']}(Remote)"
        summary = " ⟶ ".join([*jump_parts, remote_part])

        return {
            "summary": summary,
            "hosts": [
                Host(
                    summary=host.get("summary"),
                    ip=host["ip"],
                    username=host["username"],
                    password=host["password"],
                    remote=host["remote"],
                    jump=host["jump"],
                    jump_order=host["jump_order"],
                )
                for host in [*jump_hosts, remote_host]
            ],
        }

    def _get_route_summary(self, route_data: dict[str, Any]) -> str:
        """Get route summary string."""
        return (
            route_data.get("summary", str(route_data))
            if isinstance(route_data, dict)
            else getattr(route_data, "summary", str(route_data))
        )
