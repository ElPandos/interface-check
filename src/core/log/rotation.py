"""Log rotation utilities for managing log file sizes."""

import logging
from pathlib import Path

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
    if "logger_flap_states" not in shared_flap_state:
        shared_flap_state["logger_flap_states"] = {}


def _should_logger_rotate(logger_key: str, shared_flap_state: dict) -> bool:
    """Check if specific logger should rotate based on its flap state.

    Args:
        logger_key: Logger identifier
        shared_flap_state: Shared state dict

    Returns:
        True if logger should rotate (has pending flap)
    """
    logger_states = shared_flap_state.get("logger_flap_states", {})
    return logger_states.get(logger_key, False)


def _mark_logger_for_rotation(logger_key: str, shared_flap_state: dict) -> None:
    """Mark logger as needing rotation due to flap.

    Args:
        logger_key: Logger identifier
        shared_flap_state: Shared state dict
    """
    main_logger = logging.getLogger("main")
    if "logger_flap_states" not in shared_flap_state:
        shared_flap_state["logger_flap_states"] = {}
    shared_flap_state["logger_flap_states"][logger_key] = True
    main_logger.debug(f"Rotation: Marked {logger_key} for rotation (flap detected)")


def _clear_logger_flap_state(logger_key: str, shared_flap_state: dict, has_rotated_since_flap: dict[str, bool]) -> None:
    """Clear flap state for specific logger after rotation.

    Args:
        logger_key: Logger identifier
        shared_flap_state: Shared state dict
        has_rotated_since_flap: Rotation tracking dict
    """
    logger_states = shared_flap_state.get("logger_flap_states", {})
    if logger_key in logger_states:
        logger_states[logger_key] = False
    has_rotated_since_flap[logger_key] = False


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

    Rotation logic (per-logger):
    - If logger marked for rotation (flap occurred while filling): Rotate to new file
    - Otherwise: Clear file and reuse
    - Each logger tracks its own flap state independently

    Args:
        logger: Logger to check
        max_size_kb: Maximum log size in KB
        shared_flap_state: Dict with 'logger_flap_states' per logger
        has_rotated_since_flap: Dict tracking rotation state per logger
        log_rotation_count: Dict tracking rotation count per logger
        keep_header: Whether to preserve CSV header when clearing
        csv_header: CSV header string (required if keep_header=True)
        timeout_sec: Timeout in seconds (unused, kept for compatibility)
    """
    main_logger = logging.getLogger("main")
    log_file = _get_log_file(logger)
    if not log_file:
        return

    logger_key = logger.name
    file_size_kb = log_file.stat().st_size / 1024 if log_file.exists() else 0
    should_rotate = _should_rotate(log_file, max_size_kb)
    flap_state = _should_logger_rotate(logger_key, shared_flap_state)

    main_logger.debug(
        f"Rotation check: {logger_key} size={file_size_kb:.1f}KB "
        f"limit={max_size_kb}KB should_rotate={should_rotate} flap_marked={flap_state}"
    )

    if not should_rotate:
        return

    _init_rotation_state(logger_key, has_rotated_since_flap, log_rotation_count, shared_flap_state)

    # Check if THIS logger should rotate based on its own flap state
    if flap_state:
        # This logger was filling during a flap - rotate to preserve data
        main_logger.info(
            f"Rotation: {logger_key} rotating to _{log_rotation_count[logger_key] + 1} "
            f"(size={file_size_kb:.1f}KB, flap_marked=True)"
        )
        _rotate_to_new_file(log_file, logger, logger_key, log_rotation_count, keep_header, csv_header)
        # Clear this logger's flap state after rotation
        _clear_logger_flap_state(logger_key, shared_flap_state, has_rotated_since_flap)
    else:
        # No flap for this logger - clear and reuse
        main_logger.info(f"Rotation: {logger_key} clearing file (size={file_size_kb:.1f}KB, flap_marked=False)")
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
    new_log_file = log_file.with_name(f"{base_stem}_{log_rotation_count[logger_key]}: {log_file.suffix}")

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
