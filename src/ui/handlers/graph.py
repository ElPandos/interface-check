import datetime as dt
import logging
from typing import Any
from nicegui import ui

import plotly.graph_objects as go

from src.models.configurations import AppConfig
from src.utils.collector import PlotSampleData, WorkManager


class Graph:
    def __init__(self, work_manager: WorkManager, app_config: AppConfig, interf: str, source: str, value: str) -> None:
        self._app_config = app_config
        self._work_manager = work_manager
        self._interf = interf
        self._source = source
        self._value = value

    def _close_card(self, card: ui.card, interf: str = None, kill_worker: bool = False) -> None:
        self._card.delete()
        logging.debug("Card deleted")

    def _update_traces(self, add_x: Any, add_y: Any, index: int = 0) -> None:
        self._fig.update_traces(
            x=list(self._fig.data[index].x) + [add_x], y=list(self._fig.data[index].y) + [add_y], selector=index
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
                    go.Scatter(x=[plot_sample.get_data_x()], y=[plot_sample.get_data_y()], name=self._interf)
                )

            if y_axis_label is None:
                y_axis_label = plot_sample.get_label_y()

        worker.clear()

        self._fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            title=f"Interface: {self._interf} - Source: {self._source} - Value: {self._value}",
            # xaxis_title=f"Time",
            yaxis_title=f"{y_axis_label}",
            legend_title="Legend",
            xaxis=dict(type="date", tickformat="%d %b %H:%M:%S", tickangle=-45),
        )
        self._plot.update()

    def update_auto(self) -> None:
        if self._auto_update.value:
            self._auto_update_timer = ui.timer(self._app_config.system.get_graph_update_value(), self.update)
            logging.debug(f"Auto update enabled each: {self._app_config.system.get_graph_update_value()} sec")
        else:
            self._auto_update_timer.cancel()
            logging.debug("Auto update disabled")

    def build(self) -> None:
        self._card = ui.card().classes("w-full")
        with self._card, ui.row().classes("w-full"):
            # Build plot
            self._fig = go.Figure()
            self._plot = ui.plotly(self._fig).classes("w-full h-80")
            self._fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))

            # Buttons
            ui.button("Update graph", on_click=self.update)
            self._auto_update = ui.checkbox(f"Auto").on_value_change(lambda e: self.update_auto())
            ui.space()
            ui.button("X", on_click=lambda c=self._card: self._close_card(c))


class GraphHandler:
    _graphs: dict[str, Graph] = {}

    def __init__(self) -> None:
        pass

    def add(self, work_manager: WorkManager, app_config: AppConfig, interf: str, source: str, value: str) -> None:
        self._graphs[value] = Graph(app_config, work_manager, interf, source, value)
        self._graphs[value].build()

    def remove(self, value: str) -> None:
        self._graphs[value].remove()
        self._graphs.pop(value)
