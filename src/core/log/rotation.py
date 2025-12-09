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
    if "flaps_detected_during" not in shared_flap_state:
        shared_flap_state["flaps_detected_during"] = False
    if "active_loggers" not in shared_flap_state:
        shared_flap_state["active_loggers"] = set()


def _all_loggers_rotated(shared_flap_state: dict, has_rotated_since_flap: dict[str, bool]) -> bool:
    """Check if all active loggers have rotated.

    Args:
        shared_flap_state: Shared state dict
        has_rotated_since_flap: Rotation tracking dict

    Returns:
        True if all active loggers rotated
    """
    return all(
        has_rotated_since_flap.get(log, False) for log in shared_flap_state["active_loggers"]
    )


def _reset_rotation_cycle(
    shared_flap_state: dict, has_rotated_since_flap: dict[str, bool], log_rotation_count: dict[str, int]
) -> None:
    """Reset rotation cycle after all loggers rotated and no new flaps.

    Args:
        shared_flap_state: Shared state dict
        has_rotated_since_flap: Rotation tracking dict
        log_rotation_count: Counter dict
    """
    shared_flap_state["flaps_detected"] = False
    for log in shared_flap_state["active_loggers"]:
        has_rotated_since_flap[log] = False
        log_rotation_count[log] = 0  # Reset counter when cycle ends


def _continue_rotation_cycle(shared_flap_state: dict, has_rotated_since_flap: dict[str, bool]) -> None:
    """Continue rotation cycle when new flaps detected during rotation.

    Args:
        shared_flap_state: Shared state dict
        has_rotated_since_flap: Rotation tracking dict
    """
    shared_flap_state["flaps_detected_during"] = False
    for log in shared_flap_state["active_loggers"]:
        has_rotated_since_flap[log] = False


def check_and_rotate_log(
    logger: logging.Logger,
    max_size_kb: int,
    shared_flap_state: dict[str, bool],
    has_rotated_since_flap: dict[str, bool],
    log_rotation_count: dict[str, int],
    keep_header: bool = False,
    csv_header: str | None = None,
) -> None:
    """Check log file size and rotate if needed.

    Rotation logic:
    - If flaps_detected=True: Rotate to new file with suffix to preserve data
    - If flaps_detected=False: Clear file and reuse (no suffix increment)
    - After all loggers rotate: Check if new flaps occurred
      - If yes: Continue rotation cycle
      - If no: End cycle and reset counters

    Args:
        logger: Logger to check
        max_size_kb: Maximum log size in KB
        shared_flap_state: Dict with 'flaps_detected', 'flaps_detected_during', 'active_loggers'
        has_rotated_since_flap: Dict tracking rotation state per logger
        log_rotation_count: Dict tracking rotation count per logger
        keep_header: Whether to preserve CSV header when clearing
        csv_header: CSV header string (required if keep_header=True)
    """
    main_logger = logging.getLogger("main")
    log_file = _get_log_file(logger)
    if not log_file or not _should_rotate(log_file, max_size_kb):
        return

    logger_key = logger.name
    _init_rotation_state(logger_key, has_rotated_since_flap, log_rotation_count, shared_flap_state)
    shared_flap_state["active_loggers"].add(logger_key)

    if shared_flap_state.get("flaps_detected", False):
        # Flaps detected - rotate to new file to preserve data
        main_logger.info(
            f"Rotation: {logger_key} rotating to _{log_rotation_count[logger_key] + 1} "
            f"(flaps_detected=True, flaps_during={shared_flap_state.get('flaps_detected_during', False)})"
        )
        _rotate_to_new_file(
            log_file, logger, logger_key, log_rotation_count, keep_header, csv_header
        )
        has_rotated_since_flap[logger_key] = True

        # Check if all active loggers have rotated
        if _all_loggers_rotated(shared_flap_state, has_rotated_since_flap):
            if shared_flap_state.get("flaps_detected_during", False):
                # New flaps during rotation - continue cycle
                main_logger.info(
                    f"Rotation: All loggers rotated, new flaps detected - continuing cycle "
                    f"(active_loggers={len(shared_flap_state['active_loggers'])})"
                )
                _continue_rotation_cycle(shared_flap_state, has_rotated_since_flap)
            else:
                # No new flaps - end cycle and reset counters
                main_logger.info(
                    f"Rotation: All loggers rotated, no new flaps - ending cycle and resetting counters "
                    f"(active_loggers={len(shared_flap_state['active_loggers'])})"
                )
                _reset_rotation_cycle(shared_flap_state, has_rotated_since_flap, log_rotation_count)
    else:
        # No flaps - clear file and reuse (no suffix)
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

    # Create new file with raw CSV header (no logging prefix)
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

    # Clear file and write header if needed
    if keep_header and csv_header:
        log_file.write_text(csv_header + "\n")
    else:
        log_file.write_text("")

    new_handler = logging.FileHandler(log_file, mode="a")
    new_handler.setFormatter(create_formatter(logger.name))
    new_handler.setLevel(logger.level)
    logger.addHandler(new_handler)
