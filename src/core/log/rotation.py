"""Log rotation utilities for managing log file sizes."""

import logging
from pathlib import Path
import time

from src.core.log.formatter import create_formatter


def _get_log_file(logger: logging.Logger) -> Path | None:
    """Get log file path from logger.

    Args:
        logger: Logger instance

    Returns:
        Path to log file or None
    """
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename)
    return None


def _should_rotate(log_file: Path, max_size_kb: int) -> bool:
    """Check if log file should be rotated.

    Args:
        log_file: Log file path
        max_size_kb: Maximum size in KB

    Returns:
        True if file should be rotated
    """
    if not log_file.exists():
        return False
    return log_file.stat().st_size / 1024 >= max_size_kb


def _init_rotation_state(
    logger_key: str,
    has_rotated_since_flap: dict[str, bool],
    log_rotation_count: dict[str, int],
    shared_flap_state: dict,
) -> None:
    """Initialize rotation state dictionaries.

    Args:
        logger_key: Logger identifier
        has_rotated_since_flap: Rotation tracking dict
        log_rotation_count: Counter dict
        shared_flap_state: Shared state dict
    """
    if logger_key not in has_rotated_since_flap:
        has_rotated_since_flap[logger_key] = False
    if logger_key not in log_rotation_count:
        log_rotation_count[logger_key] = 0
    if "last_flap_time" not in shared_flap_state:
        shared_flap_state["last_flap_time"] = None


def _should_end_rotation_cycle(shared_flap_state: dict, timeout_sec: int) -> bool:
    """Check if rotation cycle should end based on time since last flap.

    Args:
        shared_flap_state: Shared state dict
        timeout_sec: Timeout in seconds

    Returns:
        True if no flaps for timeout period
    """
    last_flap = shared_flap_state.get("last_flap_time")
    if last_flap is None:
        return True
    return time.time() - last_flap > timeout_sec


def _start_rotation_cycle(shared_flap_state: dict, main_logger: logging.Logger) -> None:
    """Start new rotation cycle.

    Args:
        shared_flap_state: Shared state dict
        main_logger: Main logger for status messages
    """
    shared_flap_state["flaps_detected"] = True
    main_logger.info("Rotation: Starting new cycle (flaps detected)")


def _end_rotation_cycle(
    shared_flap_state: dict,
    has_rotated_since_flap: dict[str, bool],
    log_rotation_count: dict[str, int],
    main_logger: logging.Logger,
    timeout_sec: int,
) -> None:
    """End rotation cycle and reset flap tracking.

    Args:
        shared_flap_state: Shared state dict
        has_rotated_since_flap: Rotation tracking dict
        log_rotation_count: Counter dict (NOT reset to preserve file numbering)
        main_logger: Main logger for status messages
        timeout_sec: Timeout in seconds
    """
    shared_flap_state["flaps_detected"] = False
    shared_flap_state["last_flap_time"] = None
    for logger_key in list(has_rotated_since_flap.keys()):
        has_rotated_since_flap[logger_key] = False
        # DO NOT reset log_rotation_count to prevent overwriting old files
    main_logger.info(f"Rotation: Ending cycle (no flaps for {timeout_sec} s, counters preserved)")


def check_and_rotate_log(
    logger: logging.Logger,
    max_size_kb: int,
    shared_flap_state: dict[str, bool],
    has_rotated_since_flap: dict[str, bool],
    log_rotation_count: dict[str, int],
    keep_header: bool = False,
    csv_header: str | None = None,
    timeout_sec: int = 120,
) -> None:
    """Check log file size and rotate if needed.

    Rotation logic:
    - If flaps detected recently: Rotate to new file with suffix
    - If no flaps for timeout period: Clear file and reuse
    - Timeout period: configurable seconds since last flap

    Args:
        logger: Logger to check
        max_size_kb: Maximum log size in KB
        shared_flap_state: Dict with 'flaps_detected', 'last_flap_time'
        has_rotated_since_flap: Dict tracking rotation state per logger
        log_rotation_count: Dict tracking rotation count per logger
        keep_header: Whether to preserve CSV header when clearing
        csv_header: CSV header string (required if keep_header=True)
        timeout_sec: Timeout in seconds (default 300)
    """
    main_logger = logging.getLogger("main")
    log_file = _get_log_file(logger)
    if not log_file or not _should_rotate(log_file, max_size_kb):
        return

    logger_key = logger.name
    _init_rotation_state(logger_key, has_rotated_since_flap, log_rotation_count, shared_flap_state)

    # Check if rotation cycle should end
    if shared_flap_state.get("flaps_detected", False) and _should_end_rotation_cycle(
        shared_flap_state, timeout_sec
    ):
        _end_rotation_cycle(
            shared_flap_state, has_rotated_since_flap, log_rotation_count, main_logger, timeout_sec
        )

    # Rotate or clear based on flap state
    if shared_flap_state.get("flaps_detected", False):
        # Flaps detected recently - rotate to preserve data
        last_flap = shared_flap_state.get("last_flap_time")
        time_since_flap = int(time.time() - last_flap) if last_flap else 0
        main_logger.info(
            f"Rotation: {logger_key} rotating to _{log_rotation_count[logger_key] + 1} "
            f"(flaps_detected=True, time_since_last_flap={time_since_flap}s)"
        )
        _rotate_to_new_file(
            log_file, logger, logger_key, log_rotation_count, keep_header, csv_header
        )
        has_rotated_since_flap[logger_key] = True
    else:
        # No recent flaps - clear and reuse
        main_logger.info(f"Rotation: {logger_key} clearing file (flaps_detected=False)")
        _clear_log_file(log_file, logger, keep_header, csv_header)


def _rotate_to_new_file(
    log_file: Path,
    logger: logging.Logger,
    logger_key: str,
    log_rotation_count: dict[str, int],
    keep_header: bool,
    csv_header: str | None,
) -> None:
    """Rotate to new log file with suffix.

    Args:
        log_file: Current log file path
        logger: Logger instance
        logger_key: Logger key for tracking
        log_rotation_count: Dict tracking rotation count
        keep_header: Whether to write CSV header to new file
        csv_header: CSV header string
    """
    log_rotation_count[logger_key] += 1
    base_stem = (
        log_file.stem.rsplit("_", 1)[0]
        if "_" in log_file.stem and log_file.stem.split("_")[-1].isdigit()
        else log_file.stem
    )
    new_log_file = log_file.with_name(
        f"{base_stem}_{log_rotation_count[logger_key]}{log_file.suffix}"
    )

    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)

    if keep_header and csv_header:
        new_log_file.write_text(csv_header + "\n")

    new_handler = logging.FileHandler(new_log_file, mode="a")
    new_handler.setFormatter(create_formatter(logger.name))
    new_handler.setLevel(logger.level)
    logger.addHandler(new_handler)


def _clear_log_file(
    log_file: Path, logger: logging.Logger, keep_header: bool = False, csv_header: str | None = None
) -> None:
    """Clear log file and optionally write header.

    Args:
        log_file: Log file path
        logger: Logger instance
        keep_header: Whether to write CSV header
        csv_header: CSV header string
    """
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            logger.removeHandler(handler)

    if keep_header and csv_header:
        log_file.write_text(csv_header + "\n")
    else:
        log_file.write_text("")

    new_handler = logging.FileHandler(log_file, mode="a")
    new_handler.setFormatter(create_formatter(logger.name))
    new_handler.setLevel(logger.level)
    logger.addHandler(new_handler)
