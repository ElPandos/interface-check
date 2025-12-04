from datetime import timedelta
from pathlib import Path

import pandas as pd


def get_latest_log_dir() -> str:
    """Get the latest log directory path.

    Returns:
        str: Path to latest log directory (e.g., 'logs/20251201_135420/')
    """
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return ""

    subdirs = [d for d in logs_dir.iterdir() if d.is_dir()]
    if not subdirs:
        return ""

    latest = max(subdirs, key=lambda d: d.name)
    return f"{latest}/"


def parse_amber_ts(s):
    for fmt in ["%m/%d/%y-%H:%M:%S.%f", "%m/%d/%Y-%H:%M:%S.%f"]:
        try:
            return pd.to_datetime(s, format=fmt)
        except:
            pass
    try:
        return pd.to_datetime(s)
    except:
        return pd.NaT


# Reload data
df_flap = pd.read_csv("/mnt/data/sut_link_flap.csv")
df_amber = pd.read_csv("/mnt/data/sut_mxlink_amber.csv")
df_amber1 = pd.read_csv("/mnt/data/sut_mxlink_amber_1.csv")

df_amber_all = pd.concat([df_amber, df_amber1], ignore_index=True)

# Parse timestamps
df_flap["down_timestamp"] = pd.to_datetime(df_flap["down_timestamp"])


# find timestamp column
ts_col = None
for c in df_amber_all.columns:
    if "time" in c.lower():
        ts_col = c
        break

df_amber_all["amber_ts"] = df_amber_all[ts_col].astype(str).apply(parse_amber_ts)
df_amber_all = df_amber_all.dropna(subset=["amber_ts"]).reset_index(drop=True)

# Convert all numeric-like columns
numeric_cols = []
for c in df_amber_all.columns:
    if c not in ["amber_ts", ts_col]:
        df_amber_all[c + "_num"] = pd.to_numeric(
            df_amber_all[c].astype(str).str.replace("[^0-9.-]", "", regex=True), errors="coerce"
        )
        numeric_cols.append(c + "_num")

# Analysis window: last 10 seconds before flap
before_window = timedelta(seconds=10)

rows = []

for _, flap in df_flap.iterrows():
    down = flap["down_timestamp"]
    window_df = df_amber_all[
        (df_amber_all["amber_ts"] >= (down - before_window)) & (df_amber_all["amber_ts"] < down)
    ]
    if window_df.empty:
        continue
    # compute deltas inside window relative to first point in window
    base = window_df.iloc[0]
    last = window_df.iloc[-1]
    for col in numeric_cols:
        b = base[col]
        a = last[col]
        if pd.notna(a) and pd.notna(b):
            rows.append({"metric": col, "delta": a - b})

df_rank = pd.DataFrame(rows)
ranked = df_rank.groupby("metric")["delta"].mean().abs().sort_values(ascending=False).reset_index()

ranked.to_csv("/mnt/data/ranked_metrics.csv", index=False)

import ace_tools as tools

tools.display_dataframe_to_user("Ranked metrics (most change before flaps)", ranked.head(50))
