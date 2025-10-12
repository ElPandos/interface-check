"""Independent UI widget system for improved reusability."""

from abc import ABC, abstractmethod
from collections.abc import Callable
import logging
from typing import Any, TypeVar

from nicegui import ui

from src.core.base import Component, Observer, Result

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Widget(Component, ABC):
    """Base widget class for independent UI components."""

    def __init__(self, widget_id: str, title: str = ""):
        super().__init__(f"Widget-{widget_id}")
        self._widget_id = widget_id
        self._title = title
        self._container: ui.element | None = None
        self._visible = True
        self._enabled = True
        self._css_classes = []
        self._event_handlers: dict[str, list[Callable]] = {}

    @property
    def widget_id(self) -> str:
        return self._widget_id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        self._title = value
        self._update_title()

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value
        self._update_visibility()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._update_enabled_state()

    def _do_initialize(self) -> None:
        """Initialize widget."""
        self._build_ui()

    def _do_cleanup(self) -> None:
        """Cleanup widget."""
        if self._container:
            self._container.clear()

    @abstractmethod
    def _build_ui(self) -> None:
        """Build widget UI - override in subclasses."""

    def _update_title(self) -> None:
        """Update widget title - override if needed."""

    def _update_visibility(self) -> None:
        """Update widget visibility."""
        if self._container:
            self._container.set_visibility(self._visible)

    def _update_enabled_state(self) -> None:
        """Update widget enabled state - override if needed."""

    def add_css_class(self, css_class: str) -> None:
        """Add CSS class to widget."""
        if css_class not in self._css_classes:
            self._css_classes.append(css_class)
            if self._container:
                self._container.classes(add=css_class)

    def remove_css_class(self, css_class: str) -> None:
        """Remove CSS class from widget."""
        if css_class in self._css_classes:
            self._css_classes.remove(css_class)
            if self._container:
                self._container.classes(remove=css_class)

    def add_event_handler(self, event: str, handler: Callable) -> None:
        """Add event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    def remove_event_handler(self, event: str, handler: Callable) -> None:
        """Remove event handler."""
        if event in self._event_handlers and handler in self._event_handlers[event]:
            self._event_handlers[event].remove(handler)

    def trigger_event(self, event: str, *args, **kwargs) -> None:
        """Trigger event handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    self._logger.exception(f"Event handler failed for {event}: {e}")

    def refresh(self) -> None:
        """Refresh widget content - override if needed."""


class DataWidget(Widget, Observer, ABC):
    """Widget that observes data changes."""

    def __init__(self, widget_id: str, title: str = ""):
        super().__init__(widget_id, title)
        self._data: Any = None

    @property
    def data(self) -> Any:
        return self._data

    @data.setter
    def data(self, value: Any) -> None:
        self._data = value
        self._on_data_changed()

    def update(self, event: Any) -> None:
        """Handle data update from observable."""
        self.data = event

    @abstractmethod
    def _on_data_changed(self) -> None:
        """Handle data change - override in subclasses."""


class TableWidget(DataWidget):
    """Independent table widget."""

    def __init__(self, widget_id: str, title: str = "", columns: list[str] | None = None):
        super().__init__(widget_id, title)
        self._columns = columns or []
        self._rows: list[dict[str, Any]] = []
        self._table: ui.table | None = None
        self._selectable = False
        self._selected_rows: list[int] = []

    @property
    def columns(self) -> list[str]:
        return self._columns

    @columns.setter
    def columns(self, value: list[str]) -> None:
        self._columns = value
        self._rebuild_table()

    @property
    def rows(self) -> list[dict[str, Any]]:
        return self._rows

    @rows.setter
    def rows(self, value: list[dict[str, Any]]) -> None:
        self._rows = value
        self._update_table_data()

    @property
    def selectable(self) -> bool:
        return self._selectable

    @selectable.setter
    def selectable(self, value: bool) -> None:
        self._selectable = value
        self._rebuild_table()

    def _build_ui(self) -> None:
        """Build table UI."""
        self._container = ui.card().classes("w-full")
        with self._container:
            if self._title:
                ui.label(self._title).classes("text-lg font-bold mb-2")
            self._build_table()

    def _build_table(self) -> None:
        """Build table component."""
        if not self._columns:
            return

        table_columns = [{"name": col, "label": col, "field": col, "align": "left"} for col in self._columns]

        self._table = ui.table(
            columns=table_columns, rows=self._rows, selection="multiple" if self._selectable else None
        ).classes("w-full")

        if self._selectable:
            self._table.on_selection_change(self._on_selection_changed)

    def _rebuild_table(self) -> None:
        """Rebuild table with new configuration."""
        if self._container:
            self._container.clear()
            with self._container:
                if self._title:
                    ui.label(self._title).classes("text-lg font-bold mb-2")
                self._build_table()

    def _update_table_data(self) -> None:
        """Update table data."""
        if self._table:
            self._table.rows = self._rows
            self._table.update()

    def _on_data_changed(self) -> None:
        """Handle data change."""
        if isinstance(self._data, list):
            self.rows = self._data

    def _on_selection_changed(self, selection) -> None:
        """Handle selection change."""
        self._selected_rows = [row["index"] for row in selection.selection]
        self.trigger_event("selection_changed", self._selected_rows)

    def add_row(self, row: dict[str, Any]) -> None:
        """Add row to table."""
        self._rows.append(row)
        self._update_table_data()

    def remove_row(self, index: int) -> None:
        """Remove row from table."""
        if 0 <= index < len(self._rows):
            self._rows.pop(index)
            self._update_table_data()

    def clear_rows(self) -> None:
        """Clear all rows."""
        self._rows.clear()
        self._update_table_data()

    def get_selected_rows(self) -> list[dict[str, Any]]:
        """Get selected rows."""
        return [self._rows[i] for i in self._selected_rows if 0 <= i < len(self._rows)]


class ChartWidget(DataWidget):
    """Independent chart widget using Plotly."""

    def __init__(self, widget_id: str, title: str = "", chart_type: str = "line"):
        super().__init__(widget_id, title)
        self._chart_type = chart_type
        self._chart: ui.plotly | None = None
        self._x_data: list[Any] = []
        self._y_data: list[Any] = []
        self._x_label = "X"
        self._y_label = "Y"

    def _build_ui(self) -> None:
        """Build chart UI."""
        self._container = ui.card().classes("w-full")
        with self._container:
            if self._title:
                ui.label(self._title).classes("text-lg font-bold mb-2")
            self._build_chart()

    def _build_chart(self) -> None:
        """Build chart component."""
        import plotly.graph_objects as go

        if self._chart_type == "line":
            trace = go.Scatter(x=self._x_data, y=self._y_data, mode="lines+markers", name=self._title)
        elif self._chart_type == "bar":
            trace = go.Bar(x=self._x_data, y=self._y_data, name=self._title)
        else:
            trace = go.Scatter(x=[], y=[])

        fig = go.Figure(data=[trace])
        fig.update_layout(
            title=self._title, xaxis_title=self._x_label, yaxis_title=self._y_label, template="plotly_white"
        )

        self._chart = ui.plotly(fig).classes("w-full h-96")

    def _on_data_changed(self) -> None:
        """Handle data change."""
        if isinstance(self._data, dict):
            self._x_data = self._data.get("x", [])
            self._y_data = self._data.get("y", [])
            self._update_chart()

    def _update_chart(self) -> None:
        """Update chart data."""
        if self._chart:
            import plotly.graph_objects as go

            if self._chart_type == "line":
                trace = go.Scatter(x=self._x_data, y=self._y_data, mode="lines+markers", name=self._title)
            elif self._chart_type == "bar":
                trace = go.Bar(x=self._x_data, y=self._y_data, name=self._title)
            else:
                trace = go.Scatter(x=self._x_data, y=self._y_data)

            fig = go.Figure(data=[trace])
            fig.update_layout(
                title=self._title, xaxis_title=self._x_label, yaxis_title=self._y_label, template="plotly_white"
            )

            self._chart.figure = fig

    def set_labels(self, x_label: str, y_label: str) -> None:
        """Set axis labels."""
        self._x_label = x_label
        self._y_label = y_label
        self._update_chart()

    def set_data(self, x_data: list[Any], y_data: list[Any]) -> None:
        """Set chart data directly."""
        self._x_data = x_data
        self._y_data = y_data
        self._update_chart()


class FormWidget(Widget):
    """Independent form widget."""

    def __init__(self, widget_id: str, title: str = ""):
        super().__init__(widget_id, title)
        self._fields: dict[str, ui.element] = {}
        self._validators: dict[str, Callable[[Any], Result[None]]] = {}
        self._form_data: dict[str, Any] = {}

    def _build_ui(self) -> None:
        """Build form UI."""
        self._container = ui.card().classes("w-full p-4")
        with self._container:
            if self._title:
                ui.label(self._title).classes("text-lg font-bold mb-4")
            self._build_form()

    def _build_form(self) -> None:
        """Build form fields - override in subclasses."""

    def add_field(
        self,
        name: str,
        field_type: str,
        label: str = "",
        validator: Callable[[Any], Result[None]] | None = None,
        **kwargs,
    ) -> ui.element:
        """Add form field."""
        if validator:
            self._validators[name] = validator

        if field_type == "input":
            field = ui.input(label or name, **kwargs).classes("w-full mb-2")
            field.on_value_change(lambda e, n=name: self._on_field_changed(n, e.value))
        elif field_type == "textarea":
            field = ui.textarea(label or name, **kwargs).classes("w-full mb-2")
            field.on_value_change(lambda e, n=name: self._on_field_changed(n, e.value))
        elif field_type == "select":
            field = ui.select(kwargs.get("options", []), label=label or name).classes("w-full mb-2")
            field.on_value_change(lambda e, n=name: self._on_field_changed(n, e.value))
        elif field_type == "checkbox":
            field = ui.checkbox(label or name, **kwargs).classes("mb-2")
            field.on_value_change(lambda e, n=name: self._on_field_changed(n, e.value))
        else:
            field = ui.input(label or name, **kwargs).classes("w-full mb-2")

        self._fields[name] = field
        return field

    def _on_field_changed(self, field_name: str, value: Any) -> None:
        """Handle field value change."""
        self._form_data[field_name] = value
        self.trigger_event("field_changed", field_name, value)

    def get_field_value(self, name: str) -> Any:
        """Get field value."""
        return self._form_data.get(name)

    def set_field_value(self, name: str, value: Any) -> None:
        """Set field value."""
        if name in self._fields:
            self._fields[name].value = value
            self._form_data[name] = value

    def validate(self) -> Result[dict[str, Any]]:
        """Validate form data."""
        errors = {}

        for field_name, validator in self._validators.items():
            value = self._form_data.get(field_name)
            result = validator(value)
            if not result.success:
                errors[field_name] = result.error

        if errors:
            return Result.fail(f"Validation errors: {errors}")

        return Result.ok(self._form_data.copy())

    def clear(self) -> None:
        """Clear form data."""
        for field in self._fields.values():
            if hasattr(field, "value"):
                field.value = ""
        self._form_data.clear()
