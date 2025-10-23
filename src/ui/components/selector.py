"""
Generic selector component for choosing from available options.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from nicegui import ui

T = TypeVar("T")


class SelectionProvider[T](ABC):
    """Abstract provider for selection options."""

    @abstractmethod
    def get_options(self) -> list[dict[str, Any]]:
        """Get available options as list of dicts with 'label' and 'value' keys."""

    @abstractmethod
    def is_available(self, value: T) -> bool:
        """Check if option is available for selection."""


class Selector[T]:
    """Generic selector component for choosing from available options."""

    def __init__(
        self,
        provider: SelectionProvider[T],
        on_selection_change: Callable[[T | None], None] | None = None,
        label: str = "Select Option",
        classes: str = "w-64",
    ):
        self._provider = provider
        self._on_selection_change = on_selection_change
        self._label = label
        self._classes = classes
        self._selected_value: T | None = None
        self._selector: ui.select | None = None

    def build(self) -> ui.select:
        """Build selector dropdown."""
        options = self._provider.get_options()

        # Convert options to simple list for ui.select
        select_options = [opt["label"] for opt in options]

        self._selector = ui.select(options=select_options, value=None, label=self._label).classes(
            self._classes
        )

        # Store the mapping for value conversion
        self._option_mapping = {opt["label"]: opt["value"] for opt in options}

        self._selector.on_value_change(self._on_selection_change_wrapper)
        return self._selector

    def refresh(self) -> None:
        """Refresh selector options."""
        if self._selector:
            options = self._provider.get_options()
            select_options = [opt["label"] for opt in options]
            self._option_mapping = {opt["label"]: opt["value"] for opt in options}
            self._selector.options = select_options

    @property
    def selected_value(self) -> T | None:
        """Get currently selected value."""
        return self._selected_value

    def set_value(self, value: T | None) -> None:
        """Set selected value programmatically."""
        self._selected_value = value
        if self._selector and hasattr(self, "_option_mapping"):
            # Find label for value
            label = None
            for lbl, val in self._option_mapping.items():
                if val == value:
                    label = lbl
                    break
            self._selector.value = label

    def _on_selection_change_wrapper(self, e: Any) -> None:
        """Handle selection change with label to value mapping."""
        if e.value and hasattr(self, "_option_mapping"):
            actual_value = self._option_mapping.get(e.value)
            self._selected_value = actual_value
            if self._on_selection_change:
                self._on_selection_change(actual_value)
        else:
            self._selected_value = None
            if self._on_selection_change:
                self._on_selection_change(None)


class ConnectionSelectionProvider(SelectionProvider[int]):
    """Selection provider for connection routes."""

    def __init__(self, connected_routes: set[int], routes: list[dict[str, str]]):
        self._connected_routes = connected_routes
        self._routes = routes

    def get_options(self) -> list[dict[str, Any]]:
        """Get available connection options."""
        options = []
        for i in self._connected_routes:
            if i < len(self._routes):
                ssh_route = self._routes[i]
                options.append(
                    {"label": ssh_route["summary"], "value": i, "tooltip": ssh_route["summary"]}
                )
        return options

    def is_available(self, value: int) -> bool:
        """Check if connection is available."""
        return value in self._connected_routes and value < len(self._routes)

    def update_connections(self, connected_routes: set[int], routes: list[dict[str, str]]) -> None:
        """Update connection data."""
        self._connected_routes = connected_routes
        self._routes = routes


class InterfaceSelectionProvider(SelectionProvider[str]):
    """Selection provider for network interfaces."""

    def __init__(self, interfaces: list[str]):
        self._interfaces = interfaces

    def get_options(self) -> list[dict[str, Any]]:
        """Get available interface options."""
        return [
            {"label": iface, "value": iface, "tooltip": f"Network interface {iface}"}
            for iface in self._interfaces
        ]

    def is_available(self, value: str) -> bool:
        """Check if interface is available."""
        return value in self._interfaces

    def update_interfaces(self, interfaces: list[str]) -> None:
        """Update interface list."""
        self._interfaces = interfaces
