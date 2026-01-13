import logging
from typing import Any

from nicegui import ui
import plotly.graph_objects as go

from src.core.sample import PlotSampleData
from src.core.worker import WorkManager
from src.models.config import Config

logger = logging.getLogger(LogName.MAIN.value)


class GraphView:
    """Graph view for displaying worker data.

    Args:
        work_manager: Worker manager instance
        cfg: Application configuration
        interface: Network interface name
        source: Data source
        value: Value to plot
    """

    def __init__(self, work_manager: WorkManager, cfg: Config, interface: str, source: str, value: str) -> None:
        """Initialize graph view.

        Args:
            work_manager: Worker manager instance
            cfg: Application configuration
            interface: Network interface name
            source: Data source
            value: Value to plot
        """
        self._cfg = cfg
        self._work_manager = work_manager
        self._interface = interface
        self._source = source
        self._value = value

    def _close_card(self, card: ui.card) -> None:
        """Close graph card.

        Args:
            card: Card to close
        """
        card.delete()
        logger.debug("Card deleted")

    def _update_traces(self, add_x: Any, add_y: Any) -> None:
        """Update graph traces.

        Args:
            add_x: X value to add
            add_y: Y value to add
        """
        self._fig.update_traces(
            x=[*list(self._fig.data[0].x), add_x], y=[*list(self._fig.data[0].y), add_y], selector=0
        )

    def update(self) -> None:
        """Update graph with new data."""
        worker = self._work_manager.get_worker(self._interface)
        samples = worker.get_all_samples()

        y_axis_label = None
        for i in samples:
            plot_sample = PlotSampleData(i, self._source, self._value)
            if len(self._fig.data) > 0:
                self._update_traces(plot_sample.get_data_x(), plot_sample.get_data_y())
            else:
                self._fig.add_trace(
                    go.Scatter(
                        x=[plot_sample.x()],
                        y=[plot_sample.y()],
                        name=self._interface,
                    )
                )

            if y_axis_label is None:
                y_axis_label = plot_sample.y_label()

        worker.clear()

        self._fig.update_layout(
            margin={"l": 10, "r": 10, "t": 30, "b": 10},
            title=f"Interface: {self._interface} - Source: {self._source} - Value: {self._value}",
            xaxis_title="",
            yaxis_title=y_axis_label,
            legend_title="Legend",
            xaxis={"type": "date", "tickformat": "%d %b %H:%M:%S", "tickangle": -45},
        )
        self._plot.update()

    def update_auto(self) -> None:
        """Toggle auto-update."""
        if self._auto_update.value:
            self._auto_update_timer = ui.timer(self._cfg.gui.get_graph_update_value(), self.update)
            logger.debug(f"Auto update enabled each: {self._cfg.gui.get_graph_update_value()}s")
        else:
            self._auto_update_timer.cancel()
            logger.debug("Auto update disabled")

    def build(self) -> None:
        """Build graph UI."""
        self._card = ui.card().classes("w-full")
        with self._card, ui.row().classes("w-full"):
            # Build plot
            self._fig = go.Figure()
            self._plot = ui.plotly(self._fig).classes("w-full h-80")
            self._fig.update_layout(margin={"l": 10, "r": 10, "t": 30, "b": 10})

            # Buttons
            ui.button("Update graph", on_click=self.update)
            self._auto_update = ui.checkbox("Auto").on_value_change(self.update_auto)
            ui.space()
            ui.button("X", on_click=lambda c=self._card: self._close_card(c))


class GraphHandler:
    """Manages multiple graph views."""

    def __init__(self) -> None:
        """Initialize graph handler."""
        self._graphs: dict[str, GraphView] = {}

    def add(self, work_manager: WorkManager, cfg: Config, interface: str, source: str, value: str) -> None:
        """Add new graph.

        Args:
            work_manager: Worker manager instance
            cfg: Application configuration
            interface: Network interface name
            source: Data source
            value: Value to plot
        """
        self._graphs[value] = GraphView(work_manager, config, interf, source, value)
        self._graphs[value].build()

    def remove(self, value: str) -> None:
        """Remove graph.

        Args:
            value: Graph identifier
        """
        del self._graphs[value]
