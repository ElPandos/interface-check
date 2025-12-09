from datetime import timedelta
import logging

import pandas as pd
import plotly.graph_objects as go

from src.core.helpers import (
    get_files_with_prefix,
    get_latest_log_dir,
    strip_log_file,
)
from src.core.log.formatter import create_formatter
from src.platform.enums.log import LogName

# ---------------------------------------------------------------------------- #
#                             Logging configuration                            #
# ---------------------------------------------------------------------------- #

main_logger = logging.getLogger(LogName.MAIN.value)
main_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(create_formatter(LogName.MAIN.value))
main_logger.addHandler(console_handler)

# ---------------------------------------------------------------------------- #
#                            Helper Functions                                  #
# ---------------------------------------------------------------------------- #


def normalize_metric(series: pd.Series) -> pd.Series:
    """Normalize metric to 0-1 range for comparison.

    Args:
        series: Metric values to normalize

    Returns:
        Normalized series (0-1 range)
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)


def interpolate_to_master_timeline(
    df: pd.DataFrame, master_timeline: pd.DatetimeIndex
) -> pd.DataFrame:
    """Interpolate dataframe to match master timeline.

    Args:
        df: DataFrame with timestamp column
        master_timeline: Target timeline to interpolate to

    Returns:
        DataFrame reindexed and interpolated to master timeline
    """
    # Remove duplicate timestamps by keeping first occurrence
    df_clean = df.drop_duplicates(subset=["timestamp"], keep="first")
    df_indexed = df_clean.set_index("timestamp").sort_index()
    df_reindexed = df_indexed.reindex(df_indexed.index.union(master_timeline)).sort_index()
    df_interpolated = df_reindexed.interpolate(method="time")
    result = df_interpolated.reindex(master_timeline).reset_index()
    result.rename(columns={"index": "timestamp"}, inplace=True)
    return result


def create_flap_window_plot(
    flap_idx: int,
    flap_data: dict,
    df_metrics: pd.DataFrame,
    metric_cols: list[str],
    window_sec: int = 5,
) -> go.Figure:
    """Create plot showing metrics before a specific link flap.

    Args:
        flap_idx: Flap event index
        flap_data: Dict with down_timestamp, up_timestamp, interface
        df_metrics: DataFrame with timestamp and metric columns
        metric_cols: List of metric column names to plot
        window_sec: Seconds before flap to show

    Returns:
        Plotly figure with normalized metrics and flap markers
    """
    down_time = flap_data["down_timestamp"]
    up_time = flap_data.get("up_timestamp")
    interface = flap_data.get("interface", "unknown")

    # Get data window before flap
    window_start = down_time - timedelta(seconds=window_sec)
    window_df = df_metrics[
        (df_metrics["timestamp"] >= window_start) & (df_metrics["timestamp"] <= down_time)
    ].copy()

    if window_df.empty:
        return None

    # Create figure
    fig = go.Figure()

    # Plot each metric (normalized)
    for col in metric_cols:
        if col in window_df.columns:
            normalized = normalize_metric(window_df[col])
            fig.add_trace(
                go.Scatter(
                    x=window_df["timestamp"],
                    y=normalized,
                    mode="lines+markers",
                    name=col.replace("_num", ""),
                    line=dict(width=2),
                )
            )

    # Add vertical line at flap down time
    fig.add_shape(
        type="line",
        x0=down_time,
        x1=down_time,
        y0=0,
        y1=1,
        yref="paper",
        line=dict(color="red", width=3, dash="dash"),
    )
    fig.add_annotation(
        x=down_time,
        y=1,
        yref="paper",
        text="Link Down",
        showarrow=False,
        yshift=10,
        font=dict(color="red"),
    )

    # Add vertical line at flap up time if available
    if up_time and pd.notna(up_time):
        fig.add_shape(
            type="line",
            x0=up_time,
            x1=up_time,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="green", width=3, dash="dash"),
        )
        fig.add_annotation(
            x=up_time,
            y=1,
            yref="paper",
            text="Link Up",
            showarrow=False,
            yshift=10,
            font=dict(color="green"),
        )

    fig.update_layout(
        title=f"Flap #{flap_idx + 1} - Interface: {interface} - {down_time}",
        xaxis_title="Time",
        yaxis_title="Normalized Value (0-1)",
        height=500,
        hovermode="x unified",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    return fig


def create_master_timeline_plot(
    df_flaps: pd.DataFrame, df_metrics: pd.DataFrame, metric_cols: list[str], top_n: int = 5
) -> go.Figure:
    """Create master timeline showing all flaps and top metrics.

    Args:
        df_flaps: DataFrame with flap events
        df_metrics: DataFrame with timestamp and metric columns
        metric_cols: List of metric column names
        top_n: Number of top metrics to show

    Returns:
        Plotly figure with master timeline
    """
    fig = go.Figure()

    # Plot top N metrics (normalized)
    for col in metric_cols[:top_n]:
        if col in df_metrics.columns:
            normalized = normalize_metric(df_metrics[col])
            fig.add_trace(
                go.Scatter(
                    x=df_metrics["timestamp"],
                    y=normalized,
                    mode="lines",
                    name=col.replace("_num", ""),
                    line=dict(width=1.5),
                )
            )

    # Add shaded rectangles and lines for each flap duration
    for idx, flap in df_flaps.iterrows():
        down_time = flap["down_timestamp"]
        up_time = flap.get("up_timestamp")

        # Add shaded rectangle for flap duration if up_timestamp exists
        if up_time and pd.notna(up_time):
            fig.add_shape(
                type="rect",
                x0=down_time,
                x1=up_time,
                y0=0,
                y1=1,
                yref="paper",
                fillcolor="rgba(255, 0, 0, 0.2)",  # Light red with transparency
                line=dict(width=0),
                layer="below",
            )

        # Add vertical line at down time
        fig.add_shape(
            type="line",
            x0=down_time,
            x1=down_time,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="red", width=2, dash="dash"),
        )

        # Add annotation
        fig.add_annotation(
            x=down_time,
            y=1,
            yref="paper",
            text=f"Flap {idx + 1}",
            showarrow=False,
            yshift=10,
            font=dict(color="red", size=10),
        )

    fig.update_layout(
        title=f"Master Timeline - All Flaps and Top {top_n} Metrics",
        xaxis_title="Time",
        yaxis_title="Normalized Value (0-1)",
        height=600,
        hovermode="x unified",
        showlegend=True,
    )

    return fig


# ---------------------------------------------------------------------------- #
#                                MAIN function                                 #
# ---------------------------------------------------------------------------- #


def main():
    # Get latest log directory (e.g., logs/20251204_122504/)
    latest_folder = get_latest_log_dir()

    # === STEP 1: Process link flap log ===
    # Strip logging prefix from flap log and convert to CSV
    flap_log = f"{latest_folder}{LogName.SUT_LINK_FLAP.value}.log"
    flap_csv = f"{latest_folder}{LogName.SUT_LINK_FLAP.value}.csv"
    strip_log_file(flap_log, flap_csv)

    # Load flap events with timestamps
    df_flap = pd.read_csv(flap_csv)
    df_flap["down_timestamp"] = pd.to_datetime(df_flap["down_timestamp"])

    # === STEP 2: Process all other log files ===
    # Define logs to skip (not needed for analysis)
    skip_logs = {
        LogName.SUT_MXLINK_AMBER.value,  # Amber-specific data (subset of mxlink)
        LogName.SUT_LINK_FLAP.value,  # Already processed above
        LogName.MAIN.value,  # Application logs
        LogName.MEMORY.value,  # Memory usage logs
        LogName.SUT_SYSTEM_INFO.value,  # System info logs
        LogName.SLX_EYE.value,  # SLX eye scan logs
        LogName.SLX_DSC.value,  # SLX DSC logs
    }

    # Collect CSV paths for each log type
    log_csv_files: dict[str, list[str]] = {}

    for log in LogName:
        # Skip logs not needed for analysis
        if log.value in skip_logs:
            continue

        # Find all log files for this type (e.g., sut_ethtool.log, sut_ethtool_1.log)
        files = get_files_with_prefix(latest_folder, log.value)

        # Filter: exclude files with skip patterns in name and empty files
        filtered_files = [
            f
            for f in files
            if not any(skip in f.stem for skip in skip_logs) and f.stat().st_size > 0
        ]

        # Convert each log file to CSV by stripping logging prefix
        for f in filtered_files:
            csv_path = f"{latest_folder}{f.stem}.csv"
            strip_log_file(f, csv_path)
            log_csv_files.setdefault(log.value, []).append(csv_path)

    # === STEP 3: Load and combine ethtool data ===
    # Concatenate all ethtool CSV files into single dataframe
    ethtool_dfs = [pd.read_csv(csv) for csv in log_csv_files.get(LogName.SUT_ETHTOOL.value, [])]
    if not ethtool_dfs:
        main_logger.error("No ethtool data found")
        return

    df_ethtool = pd.concat(ethtool_dfs, ignore_index=True)

    # Find timestamp column (flexible column name matching)
    ts_col = next((c for c in df_ethtool.columns if "time" in c.lower()), None)
    if not ts_col:
        main_logger.error("No timestamp column found in ethtool data")
        return

    # Parse timestamps
    df_ethtool["timestamp"] = pd.to_datetime(df_ethtool[ts_col])
    df_ethtool = df_ethtool.dropna(subset=["timestamp"]).reset_index(drop=True)

    # === STEP 4: Convert all columns to numeric ===
    # Extract numeric values from all non-timestamp columns
    numeric_cols = []
    for col in df_ethtool.columns:
        if col not in ["timestamp", ts_col]:
            # Strip non-numeric characters and convert
            df_ethtool[f"{col}_num"] = pd.to_numeric(
                df_ethtool[col].astype(str).str.replace("[^0-9.-]", "", regex=True), errors="coerce"
            )
            numeric_cols.append(f"{col}_num")

    # === STEP 5: Analyze metric changes before flaps ===
    # Look at last 5 seconds before each flap event
    before_window = timedelta(seconds=5)
    rows = []

    for _, flap in df_flap.iterrows():
        down_time = flap["down_timestamp"]

        # Get ethtool data in window before flap
        window_df = df_ethtool[
            (df_ethtool["timestamp"] >= (down_time - before_window))
            & (df_ethtool["timestamp"] < down_time)
        ]

        if window_df.empty:
            continue

        # Calculate delta: last value - first value in window
        base = window_df.iloc[0]
        last = window_df.iloc[-1]

        for col in numeric_cols:
            base_val = base[col]
            last_val = last[col]
            if pd.notna(base_val) and pd.notna(last_val):
                rows.append({"metric": col, "delta": last_val - base_val})

    # === STEP 6: Rank metrics by average change ===
    if not rows:
        main_logger.warning("No metric changes found before flaps")
        return

    df_rank = pd.DataFrame(rows)
    # Group by metric, calculate mean absolute delta, sort descending
    ranked = (
        df_rank.groupby("metric")["delta"].mean().abs().sort_values(ascending=False).reset_index()
    )

    # === STEP 7: Save and display results ===
    output_file = f"{latest_folder}ranked_metrics.csv"
    ranked.to_csv(output_file, index=False)

    main_logger.info(f"Ranked metrics saved to: {output_file}")
    main_logger.info("\nTop metrics with most change before flaps:")
    main_logger.info(f"\n{ranked.head(50).to_string()}")

    # === STEP 8: Create visualization ===
    top_n = 5
    top_metrics = ranked.head(top_n)

    fig = go.Figure(
        [
            go.Bar(
                x=top_metrics["delta"],
                y=top_metrics["metric"],
                orientation="h",
                marker=dict(color="indianred"),
            )
        ]
    )

    fig.update_layout(
        title=f"Top {top_n} Metrics with Most Change Before Link Flaps",
        xaxis_title="Average Absolute Change",
        yaxis_title="Metric",
        height=600,
        yaxis=dict(autorange="reversed"),
    )

    html_file = f"{latest_folder}ranked_metrics.html"
    fig.write_html(html_file)
    main_logger.info(f"Visualization saved to: {html_file}")

    # === STEP 9: Create time-series plots for each flap ===
    main_logger.info("\nCreating time-series visualizations...")

    # Parse up_timestamp if exists
    if "up_timestamp" in df_flap.columns:
        df_flap["up_timestamp"] = pd.to_datetime(df_flap["up_timestamp"], errors="coerce")

    # Create master timeline with 1-second resolution
    time_min = df_ethtool["timestamp"].min()
    time_max = df_ethtool["timestamp"].max()
    master_timeline = pd.date_range(start=time_min, end=time_max, freq="1s")

    # Interpolate metrics to master timeline
    main_logger.info("Interpolating metrics to master timeline...")
    df_interpolated = interpolate_to_master_timeline(
        df_ethtool[["timestamp"] + numeric_cols], master_timeline
    )

    # Get top metrics for focused analysis
    top_metrics = ranked.head(10)["metric"].tolist()

    # Create individual flap plots
    for idx, flap in df_flap.iterrows():
        flap_data = {
            "down_timestamp": flap["down_timestamp"],
            "up_timestamp": flap.get("up_timestamp"),
            "interface": flap.get("interface", "unknown"),
        }

        fig_flap = create_flap_window_plot(
            idx, flap_data, df_interpolated, top_metrics, window_sec=5
        )

        if fig_flap:
            flap_html = f"{latest_folder}flap_{idx + 1}_analysis.html"
            fig_flap.write_html(flap_html)
            main_logger.info(f"Flap #{idx + 1} visualization saved to: {flap_html}")

    # Create master timeline plot
    main_logger.info("Creating master timeline plot...")
    fig_master = create_master_timeline_plot(df_flap, df_interpolated, top_metrics, top_n=5)
    master_html = f"{latest_folder}master_timeline.html"
    fig_master.write_html(master_html)
    main_logger.info(f"Master timeline saved to: {master_html}")
    try:
        fig_master.show()
    except Exception:
        pass

    # === STEP 10: Create individual metric master timelines (non-normalized) ===
    main_logger.info("\nCreating individual metric master timelines...")

    # Get original column names (without _num suffix)
    original_cols = [col for col in df_ethtool.columns if col not in ["timestamp", ts_col]]

    for col in original_cols:
        col_num = f"{col}_num"
        if col_num not in df_interpolated.columns:
            continue

        fig = go.Figure()

        # Plot raw metric values
        fig.add_trace(
            go.Scatter(
                x=df_interpolated["timestamp"],
                y=df_interpolated[col_num],
                mode="lines",
                name=col,
                line=dict(width=1.5, color="blue"),
            )
        )

        # Add flap markers
        for idx, flap in df_flap.iterrows():
            down_time = flap["down_timestamp"]
            up_time = flap.get("up_timestamp")

            # Shaded rectangle for flap duration
            if up_time and pd.notna(up_time):
                fig.add_shape(
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

            # Vertical line at down time
            fig.add_shape(
                type="line",
                x0=down_time,
                x1=down_time,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="red", width=2, dash="dash"),
            )

        fig.update_layout(
            title=f"Master Timeline - {col}",
            xaxis_title="Time",
            yaxis_title=col,
            height=500,
            hovermode="x unified",
        )

        metric_html = f"{latest_folder}master_timeline_{col}.html"
        fig.write_html(metric_html)
        main_logger.info(f"  {col}: {metric_html}")

    main_logger.info("\nAnalysis complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        main_logger.info("\nAnalysis interrupted by user")
    except Exception as e:
        main_logger.exception(f"Analysis failed: {e}")
