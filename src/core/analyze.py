"""Log data analysis and visualization."""

import logging
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.core.helpers import get_files_with_prefix, strip_log_file
from src.platform.enums.log import LogName


class AnalyzeGraphs:
    """Analyze and visualize log data with flap and tx_error markers."""

    SKIP_LOGS = frozenset(
        {
            LogName.SUT_MXLINK_AMBER.value,
            LogName.SUT_LINK_FLAP.value,
            LogName.MAIN.value,
            LogName.MEMORY.value,
            LogName.SUT_SYSTEM_INFO.value,
            LogName.SLX_EYE.value,
            LogName.SLX_DSC.value,
        }
    )

    def __init__(self, log_dir: str, logger: logging.Logger) -> None:
        self.log_dir = Path(log_dir)
        self.logger = logger
        self.df_flaps = pd.DataFrame()
        self.df_tx_errors: pd.DataFrame | None = None
        self.all_dfs: dict[str, pd.DataFrame] = {}
        self.master_timeline: pd.DatetimeIndex | None = None

    @staticmethod
    def normalize_metric(series: pd.Series) -> pd.Series:
        """Normalize metric to 0-1 range."""
        min_val = series.min()
        max_val = series.max()
        if max_val == min_val:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - min_val) / (max_val - min_val)

    @staticmethod
    def interpolate_to_timeline(df: pd.DataFrame, timeline: pd.DatetimeIndex) -> pd.DataFrame:
        """Interpolate dataframe to match timeline."""
        df_clean = df.drop_duplicates(subset=["timestamp"], keep="first").sort_values("timestamp")

        # Get actual data range to avoid extrapolation
        data_start = df_clean["timestamp"].min()
        data_end = df_clean["timestamp"].max()

        timeline_df = pd.DataFrame({"timestamp": timeline})
        result = pd.merge_asof(timeline_df, df_clean, on="timestamp", direction="nearest")

        # Set values outside actual data range to NaN (no extrapolation)
        numeric_cols = result.select_dtypes(include=["number"]).columns.tolist()
        if numeric_cols:
            mask = (result["timestamp"] < data_start) | (result["timestamp"] > data_end)
            result.loc[mask, numeric_cols] = pd.NA

            # Time-weighted interpolation within data range
            result_indexed = result.set_index("timestamp")
            result_indexed[numeric_cols] = result_indexed[numeric_cols].interpolate(method="time")
            result = result_indexed.reset_index()

        return result

    @staticmethod
    def add_event_markers(fig: go.Figure, df_flaps: pd.DataFrame, df_tx_errors: pd.DataFrame | None = None) -> None:
        """Add flap and tx_error markers to figure."""
        shapes = []

        if not df_flaps.empty:
            for down_time, up_time in zip(
                df_flaps["down_timestamp"],
                df_flaps.get("up_timestamp", [None] * len(df_flaps)),
                strict=False,
            ):
                if up_time and pd.notna(up_time):
                    shapes.append(
                        dict(
                            type="rect",
                            x0=down_time,
                            x1=up_time,
                            y0=0,
                            y1=1,
                            yref="paper",
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            line=dict(width=0),
                            layer="below",
                        )
                    )

                shapes.append(
                    dict(
                        type="line",
                        x0=down_time,
                        x1=down_time,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dash"),
                    )
                )

        if df_tx_errors is not None and not df_tx_errors.empty:
            for timestamp in df_tx_errors["timestamp"]:
                shapes.append(
                    dict(
                        type="line",
                        x0=timestamp,
                        x1=timestamp,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color="yellow", width=2, dash="dot"),
                    )
                )

        fig.update_layout(shapes=shapes)

    def load_flaps(self) -> None:
        """Load link flap events."""
        flap_log = self.log_dir / f"{LogName.SUT_LINK_FLAP.value}.log"
        flap_csv = self.log_dir / f"{LogName.SUT_LINK_FLAP.value}.csv"

        if not flap_log.exists():
            self.logger.warning(f"Flap log file not found: {flap_log}")
            self.df_flaps = pd.DataFrame(columns=["down_timestamp", "up_timestamp", "interface", "duration"])
            return

        strip_log_file(flap_log, flap_csv)

        try:
            self.df_flaps = pd.read_csv(flap_csv)
            if not self.df_flaps.empty:
                self.df_flaps["down_timestamp"] = pd.to_datetime(self.df_flaps["down_timestamp"])
                if "up_timestamp" in self.df_flaps.columns:
                    self.df_flaps["up_timestamp"] = pd.to_datetime(self.df_flaps["up_timestamp"], errors="coerce")
        except (pd.errors.EmptyDataError, FileNotFoundError):
            self.logger.warning("No link flap events found")
            self.df_flaps = pd.DataFrame(columns=["down_timestamp", "up_timestamp", "interface", "duration"])

    def load_logs(self) -> None:
        """Load and process all log files."""
        log_csv_files: dict[str, list[Path]] = {}

        for log in LogName:
            if log.value in self.SKIP_LOGS:
                continue

            files = get_files_with_prefix(str(self.log_dir), log.value)
            filtered_files = [
                f for f in files if not any(skip in f.stem for skip in self.SKIP_LOGS) and f.stat().st_size > 0
            ]

            for f in filtered_files:
                csv_path = self.log_dir / f"{f.stem}.csv"
                strip_log_file(f, csv_path)
                log_csv_files.setdefault(log.value, []).append(csv_path)

        for log_name, csv_files in log_csv_files.items():
            if not csv_files:
                continue
            try:
                dfs = []
                for csv_file in csv_files:
                    try:
                        df = pd.read_csv(csv_file, low_memory=False)
                        if not df.empty:
                            dfs.append(df)
                    except Exception as e:
                        self.logger.warning(f"Failed to load {csv_file}: {e}")

                if dfs:
                    self.all_dfs[log_name] = pd.concat(dfs, ignore_index=True, copy=False)
            except Exception as e:
                self.logger.warning(f"Failed to process {log_name}: {e}")

    def load_tx_errors(self) -> None:
        """Load tx_errors data and filter for errors > 0."""
        if LogName.SUT_TX_ERRORS.value not in self.all_dfs:
            return

        df_tx = self.all_dfs[LogName.SUT_TX_ERRORS.value]
        ts_col = next((c for c in df_tx.columns if "time" in c.lower()), None)
        if not ts_col:
            return

        df_tx["timestamp"] = pd.to_datetime(df_tx[ts_col])
        if "tx_errors" in df_tx.columns:
            df_tx["tx_errors_num"] = pd.to_numeric(df_tx["tx_errors"], errors="coerce")
            self.df_tx_errors = df_tx[df_tx["tx_errors_num"] > 0][["timestamp"]].copy()

    def prepare_dataframe(self, df: pd.DataFrame) -> tuple[pd.DataFrame | None, list[str], str | None]:
        """Prepare dataframe with timestamps and numeric columns.

        Returns:
            Tuple of (prepared_df, numeric_cols, timestamp_col)
        """
        ts_col = next((c for c in df.columns if "time" in c.lower()), None)
        if not ts_col:
            return None, [], None

        df_work = df.copy()
        df_work["timestamp"] = pd.to_datetime(df_work[ts_col], errors="coerce")
        df_work = df_work.dropna(subset=["timestamp"]).reset_index(drop=True)

        numeric_cols = []
        non_time_cols = [col for col in df_work.columns if col not in ["timestamp", ts_col]]

        for col in non_time_cols:
            col_num = f"{col}_num"
            cleaned = df_work[col].astype(str).str.extract(r"([+-]?\d*\.?\d+)", expand=False)
            df_work[col_num] = pd.to_numeric(cleaned, errors="coerce")
            numeric_cols.append(col_num)

        return df_work, numeric_cols, ts_col

    def create_master_timeline(self, df: pd.DataFrame) -> None:
        """Create master timeline from dataframe timestamps."""
        time_min = df["timestamp"].min()
        time_max = df["timestamp"].max()
        self.master_timeline = pd.date_range(start=time_min, end=time_max, freq="1s")

    def create_metric_graph(self, log_name: str, col: str, df_interp: pd.DataFrame) -> None:
        """Create and save individual metric graph."""
        col_num = f"{col}_num"
        if col_num not in df_interp.columns or df_interp[col_num].isna().all():
            return

        if df_interp[col_num].nunique() <= 1:
            self.logger.debug(f"Skipping {col} - no variation in data")
            return

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_interp["timestamp"],
                y=df_interp[col_num],
                mode="lines",
                name=col,
                line=dict(width=1.5, color="blue"),
                connectgaps=False,
            )
        )

        self.add_event_markers(fig, self.df_flaps, self.df_tx_errors)

        fig.update_layout(
            title=f"Master Timeline - {log_name} - {col}",
            xaxis_title="Time",
            yaxis_title=col,
            height=500,
            hovermode="x unified",
            showlegend=False,
        )

        metric_html = self.log_dir / f"master_timeline_{log_name}_{col}.html"
        fig.write_html(metric_html, config={"displayModeBar": False})
        self.logger.info(f"  {col}: {metric_html}")

    def create_combined_graph(self, log_name: str, df_interp: pd.DataFrame, original_cols: list[str]) -> None:
        """Create combined HTML with all metrics in subplots."""
        valid_cols = [
            col
            for col in original_cols
            if f"{col}_num" in df_interp.columns
            and not df_interp[f"{col}_num"].isna().all()
            and df_interp[f"{col}_num"].nunique() > 1
        ]

        if not valid_cols:
            self.logger.warning(f"  No valid metrics to plot for {log_name}")
            return

        rows = len(valid_cols)
        fig = make_subplots(
            rows=rows,
            cols=1,
            subplot_titles=[col for col in valid_cols],
            vertical_spacing=0.05,
            shared_xaxes=True,
        )

        for idx, col in enumerate(valid_cols, start=1):
            col_num = f"{col}_num"
            fig.add_trace(
                go.Scatter(
                    x=df_interp["timestamp"],
                    y=df_interp[col_num],
                    mode="lines",
                    name=col,
                    line=dict(width=1.5),
                    connectgaps=False,
                    showlegend=False,
                ),
                row=idx,
                col=1,
            )

        # Add event markers to all subplots
        shapes = []
        if not self.df_flaps.empty:
            for down_time, up_time in zip(
                self.df_flaps["down_timestamp"],
                self.df_flaps.get("up_timestamp", [None] * len(self.df_flaps)),
                strict=False,
            ):
                if up_time and pd.notna(up_time):
                    shapes.append(
                        dict(
                            type="rect",
                            x0=down_time,
                            x1=up_time,
                            y0=0,
                            y1=1,
                            yref="paper",
                            fillcolor="rgba(255, 0, 0, 0.2)",
                            line=dict(width=0),
                            layer="below",
                        )
                    )
                shapes.append(
                    dict(
                        type="line",
                        x0=down_time,
                        x1=down_time,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color="red", width=2, dash="dash"),
                    )
                )

        if self.df_tx_errors is not None and not self.df_tx_errors.empty:
            for timestamp in self.df_tx_errors["timestamp"]:
                shapes.append(
                    dict(
                        type="line",
                        x0=timestamp,
                        x1=timestamp,
                        y0=0,
                        y1=1,
                        yref="paper",
                        line=dict(color="yellow", width=2, dash="dot"),
                    )
                )

        fig.update_layout(
            title=f"Master Timeline - {log_name} - All Metrics",
            height=300 * rows,
            hovermode="x unified",
            shapes=shapes,
        )
        fig.update_xaxes(title_text="Time", row=rows, col=1)

        combined_html = self.log_dir / f"master_timeline_{log_name}.html"
        fig.write_html(combined_html, config={"displayModeBar": False})
        self.logger.info(f"  Combined: {combined_html}")

    def process_log(self, log_name: str, df_log: pd.DataFrame) -> None:
        """Process single log type and create graphs for all metrics."""
        self.logger.info(f"\nProcessing {log_name}...")

        df_prep, numeric_cols, ts_col = self.prepare_dataframe(df_log.copy())
        if df_prep is None:
            self.logger.warning(f"  No timestamp column in {log_name}, skipping")
            return

        df_interp = self.interpolate_to_timeline(df_prep[["timestamp"] + numeric_cols], self.master_timeline)

        original_cols = [col for col in df_log.columns if col not in ["timestamp", ts_col]]

        # Create combined graph with all metrics
        self.create_combined_graph(log_name, df_interp, original_cols)

        # Create individual graphs
        for col in original_cols:
            self.create_metric_graph(log_name, col, df_interp)

    def run(self) -> None:
        """Run complete analysis pipeline."""
        self.logger.info("Loading data...")

        try:
            self.load_flaps()
            self.load_logs()

            if not self.all_dfs:
                self.logger.error("No data found")
                return

            self.load_tx_errors()

            if LogName.SUT_ETHTOOL.value not in self.all_dfs:
                self.logger.warning("No ethtool data found, using first available log for timeline")
                if self.all_dfs:
                    first_log = next(iter(self.all_dfs.values()))
                    df_prep, _, _ = self.prepare_dataframe(first_log)
                    if df_prep is not None:
                        self.create_master_timeline(df_prep)
            else:
                df_ethtool = self.all_dfs[LogName.SUT_ETHTOOL.value]
                df_ethtool_prep, _, _ = self.prepare_dataframe(df_ethtool)
                if df_ethtool_prep is not None:
                    self.create_master_timeline(df_ethtool_prep)

            if self.master_timeline is None:
                self.logger.error("Failed to create master timeline")
                return

            self.logger.info(f"\nCreating graphs for {len(self.all_dfs)} log types...")
            for log_name, df_log in self.all_dfs.items():
                try:
                    self.process_log(log_name, df_log)
                except Exception:
                    self.logger.exception(f"Failed to process {log_name}")
                    continue

            self.logger.info("\nAnalysis complete!")

        except Exception as e:
            self.logger.exception(f"Analysis pipeline failed: {e}")
            raise
