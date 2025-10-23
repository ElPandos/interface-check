import logging
from typing import Any

from nicegui import ui
import plotly.graph_objects as go

from src.models.config import Config
from src.platform.collector import PlotSampleData, WorkManager

logger = logging.getLogger(__name__)


class GraphView:
    def __init__(
        self, work_manager: WorkManager, config: Config, interf: str, source: str, value: str
    ) -> None:
        self._config = config
        self._work_manager = work_manager
        self._interf = interf
        self._source = source
        self._value = value

    def _close_card(self, card: ui.card) -> None:
        card.delete()
        logger.debug("Card deleted")

    def _update_traces(self, add_x: Any, add_y: Any) -> None:
        self._fig.update_traces(
            x=[*list(self._fig.data[0].x), add_x], y=[*list(self._fig.data[0].y), add_y], selector=0
        )

    def update(self) -> None:
        worker = self._work_manager.get_worker(self._interf)
        samples = worker.get_all_samples()

        y_axis_label = None
        for i in samples:
            plot_sample = PlotSampleData(i, self._source, self._value)
            if len(self._fig.data) > 0:
                self._update_traces(plot_sample.get_data_x(), plot_sample.get_data_y())
            else:
                self._fig.add_trace(
                    go.Scatter(
                        x=[plot_sample.get_data_x()],
                        y=[plot_sample.get_data_y()],
                        name=self._interf,
                    )
                )

            if y_axis_label is None:
                y_axis_label = plot_sample.get_label_y()

        worker.clear()

        self._fig.update_layout(
            margin={"l": 10, "r": 10, "t": 30, "b": 10},
            title=f"Interface: {self._interf} - Source: {self._source} - Value: {self._value}",
            xaxis_title="",
            yaxis_title=y_axis_label,
            legend_title="Legend",
            xaxis={"type": "date", "tickformat": "%d %b %H:%M:%S", "tickangle": -45},
        )
        self._plot.update()

    def update_auto(self) -> None:
        if self._auto_update.value:
            self._auto_update_timer = ui.timer(
                self._config.gui.get_graph_update_value(), self.update
            )
            logger.debug(
                f"Auto update enabled each: {self._config.gui.get_graph_update_value()} sec"
            )
        else:
            self._auto_update_timer.cancel()
            logger.debug("Auto update disabled")

    def build(self) -> None:
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
    def __init__(self) -> None:
        self._graphs: dict[str, GraphView] = {}

    def add(
        self, work_manager: WorkManager, config: Config, interf: str, source: str, value: str
    ) -> None:
        self._graphs[value] = GraphView(work_manager, config, interf, source, value)
        self._graphs[value].build()

    def remove(self, value: str) -> None:
        del self._graphs[value]
