"""Refactored base UI components with dependency injection."""

from abc import ABC, abstractmethod
import logging
from typing import Any

from nicegui import ui

from src.core.lifecycle import ILifecycleAware
from src.interfaces.configuration import IConfigurationProvider
from src.interfaces.connection import IConnection
from src.interfaces.ui import IEventBus, IPanel, ITab

logger = logging.getLogger(__name__)


class BaseComponent(ABC, ILifecycleAware):
    """Base class for all UI components with lifecycle management."""

    def __init__(self, name: str, label: str, icon: str = ""):
        self._name = name
        self._label = label
        self._icon = icon
        self._built = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def label(self) -> str:
        return self._label

    @property
    def icon(self) -> str:
        return self._icon

    def initialize(self) -> None:
        """Initialize component."""
        if not self._built:
            self.build()
            self._built = True

    def cleanup(self) -> None:
        """Clean up component resources."""
        self.destroy()

    @abstractmethod
    def build(self) -> None:
        """Build the UI component."""

    def destroy(self) -> None:
        """Clean up component resources."""


class Tab(BaseComponent, ITab):
    """Refactored tab component with dependency injection."""

    def __init__(self, name: str, label: str, icon: str = "", event_bus: IEventBus | None = None):
        super().__init__(name, label, icon)
        self._event_bus = event_bus
        self._tab_element: ui.tab | None = None
        self._icon_element: ui.icon | None = None

    def build(self) -> None:
        """Build tab UI."""
        with ui.column().classes("items-center gap-1"):
            self._tab_element = ui.tab(self.name)
            if self._icon_element:
                self._icon_element.clear()
            self._icon_element = ui.icon(self.icon).props("size=24px")

        if self._event_bus:
            self._event_bus.publish("tab_created", {"name": self.name, "label": self.label})

    def destroy(self) -> None:
        """Clean up tab resources."""
        if self._tab_element:
            self._tab_element.delete()
        if self._icon_element:
            self._icon_element.delete()


class Panel(BaseComponent, IPanel):
    """Refactored panel component with dependency injection."""

    def __init__(
        self,
        name: str,
        label: str,
        icon: str = "",
        config: IConfigurationProvider | None = None,
        connection: IConnection | None = None,
        event_bus: IEventBus | None = None,
    ):
        super().__init__(name, label, icon)
        self._config = config
        self._connection = connection
        self._event_bus = event_bus
        self._panel_element: ui.tab_panel | None = None
        self._content_container: ui.column | None = None

    def build(self) -> None:
        """Build panel UI."""
        with ui.tab_panel(self.name).classes("w-full h-screen") as self._panel_element:
            self._build_header()
            self._content_container = ui.column().classes("w-full h-full")
            with self._content_container:
                self._build_content()

        if self._event_bus:
            self._event_bus.publish("panel_created", {"name": self.name, "label": self.label})

    def refresh(self) -> None:
        """Refresh panel content."""
        if self._content_container:
            self._content_container.clear()
            with self._content_container:
                self._build_content()

    def _build_header(self) -> None:
        """Build panel header."""
        with ui.row().classes("items-center gap-2 mb-4"):
            if self.icon:
                ui.icon(self.icon).props("size=24px")
            ui.label(f"Content of: {self.label}").classes("text-lg font-bold")

    @abstractmethod
    def _build_content(self) -> None:
        """Build panel content - to be implemented by subclasses."""

    def destroy(self) -> None:
        """Clean up panel resources."""
        if self._panel_element:
            self._panel_element.delete()


class ToolPanel(Panel):
    """Base class for tool-specific panels."""

    def __init__(
        self,
        name: str,
        label: str,
        icon: str = "",
        config: IConfigurationProvider | None = None,
        connection: IConnection | None = None,
        event_bus: IEventBus | None = None,
    ):
        super().__init__(name, label, icon, config, connection, event_bus)
        self._tool_results: dict[str, Any] = {}

    def _build_content(self) -> None:
        """Build tool panel content."""
        self._build_controls()
        self._build_results()

    def _build_controls(self) -> None:
        """Build tool control interface."""
        with ui.card().classes("w-full mb-4"), ui.row().classes("w-full items-center gap-4"):
            ui.label(self.label).classes("text-lg font-bold")
            ui.space()

            connection_status = (
                "Connected" if (self._connection and self._connection.is_connected()) else "Disconnected"
            )
            color = "positive" if connection_status == "Connected" else "negative"
            ui.badge(connection_status, color=color)

            ui.button("Refresh", on_click=self._on_refresh, icon="refresh")

    def _build_results(self) -> None:
        """Build results display."""
        if self._tool_results:
            with ui.card().classes("w-full"):
                ui.label("Results").classes("text-lg font-bold mb-2")
                for key, value in self._tool_results.items():
                    with ui.expansion(key, icon="data_object"):
                        ui.json_editor({"content": {"json": value}}).run_editor_method(
                            "updateProps", {"readOnly": True}
                        )
        else:
            ui.label("No results available. Click Refresh to load data.").classes("text-gray-500")

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        if self._connection and self._connection.is_connected():
            self._execute_tool_commands()
            self.refresh()
        else:
            ui.notify("No connection available", type="warning")

    @abstractmethod
    def _execute_tool_commands(self) -> None:
        """Execute tool commands - to be implemented by subclasses."""
