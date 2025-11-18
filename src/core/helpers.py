"""Common helper functions used across the project.

This module provides reusable utility functions for:
- Attribute extraction from objects
- Safe value conversion
- Common data transformations
"""

from typing import Any


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
