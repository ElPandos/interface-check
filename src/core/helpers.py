"""Common helper functions used across the project.

This module provides reusable utility functions for:
- Attribute extraction from objects
- Safe value conversion
- Common data transformations
"""

from pathlib import Path
from typing import Any

import pandas as pd


def get_attr_value(obj: Any, attr_name: str, default: str = "") -> str:
    """Safely extract attribute value from object.

    Args:
        obj: Object to extract attribute from
        attr_name: Name of attribute to extract
        default: Default value if attribute missing or None

    Returns:
        String representation of attribute value or default
    """
    if not hasattr(obj, attr_name):
        return default

    attr = getattr(obj, attr_name)
    if attr is None:
        return default

    # Handle lists (e.g., temperature with C and F, power with mW and dBm)
    if isinstance(attr, list) and len(attr) > 0:
        # Take first value (mW for power, Celsius for temperature)
        first_item = attr[0]
        if hasattr(first_item, "value"):
            value = first_item.value
            if isinstance(value, float):
                return f"{value:.6f}"
            return str(value)
        return str(first_item)

    # Handle objects with .value property (like ValueWithUnit)
    if hasattr(attr, "value"):
        value = attr.value
        # Format floats with 6 decimal places
        if isinstance(value, float):
            return f"{value:.6f}"
        return str(value)

    return str(attr)


def safe_float(value: str, default: float = 0.0) -> float:
    """Convert string to float with fallback.

    Args:
        value: String value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: str, default: int = 0) -> int:
    """Convert string to int with fallback.

    Args:
        value: String value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human-readable string.

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length with suffix.

    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


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


def get_files_with_prefix(folder: str, prefix: str) -> list[Path]:
    """Get list of files in folder that start with prefix.

    Args:
        folder: Folder path
        prefix: File name prefix (e.g., 'sut_ethtool')

    Returns:
        list[Path]: Sorted list of matching files
    """
    folder_path = Path(folder)
    if not folder_path.exists():
        return []
    return sorted(folder_path.glob(f"{prefix}*"))


def parse_amber_ts(s: str) -> pd.Timestamp:
    """Parse amber timestamp with multiple format attempts.

    Args:
        s: Timestamp string to parse

    Returns:
        pd.Timestamp: Parsed timestamp or NaT if parsing fails
    """
    for fmt in ["%m/%d/%y-%H:%M:%S.%f", "%m/%d/%Y-%H:%M:%S.%f"]:
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(s)
    except Exception:
        return pd.NaT


def strip_log_prefix(line: str) -> str:
    """Remove logging prefix from log line.

    Args:
        line: Log line with prefix

    Returns:
        str: Raw data without logging prefix
    """
    parts = line.split(" - ", 3)
    return parts[3] if len(parts) > 3 else line


def strip_log_file(input_file: str | Path, output_file: str | Path) -> None:
    """Strip logging prefix from all lines in file.

    Args:
        input_file: Input log file path
        output_file: Output file path for cleaned data
    """
    input_path = Path(input_file)
    output_path = Path(output_file)

    with input_path.open() as f_in, output_path.open("w") as f_out:
        for line in f_in:
            # Skip WARNING, ERROR, and time command output lines
            if (
                " - WARNING " in line
                or " - ERROR " in line
                or ("user" in line and "system" in line)
                or "pagefaults" in line
            ):
                continue
            f_out.write(strip_log_prefix(line.rstrip()) + "\n")


def strip_log_prefix(line: str) -> str:
    """Remove logging prefix from log line to extract raw CSV data.

    Args:
        line: Log line with prefix (e.g., '2025-12-04 12:26:13,969 - sut_link_flap - INFO - data')

    Returns:
        str: Raw data without logging prefix
    """
    parts = line.split(" - ", 3)
    return parts[3] if len(parts) > 3 else line
