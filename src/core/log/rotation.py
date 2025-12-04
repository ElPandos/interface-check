"""Log rotation utilities for managing log file sizes."""

import logging
from pathlib import Path

from src.core.log.formatter import create_formatter


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

    Two-flag rotation logic:
    - flaps_detected: Main flag indicating rotation cycle is active
    - flaps_detected_during: Secondary flag for new flaps during rotation

    Behavior:
    - If flaps_detected=True: Rotate to new file with suffix
    - After all loggers rotate: Check flaps_detected_during
      - If True: Keep flaps_detected=True, reset flaps_detected_during=False
      - If False: Reset flaps_detected=False (end cycle)
    - If flaps_detected=False: Clear file and reuse

    Args:
        logger: Logger to check
        max_size_kb: Maximum log size in KB
        shared_flap_state: Dict with 'flaps_detected', 'flaps_detected_during', 'active_loggers'
        has_rotated_since_flap: Dict tracking rotation state per logger
        log_rotation_count: Dict tracking rotation count per logger
        keep_header: Whether to preserve CSV header when clearing
        csv_header: CSV header string (required if keep_header=True)
    """
    log_file = None
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            log_file = Path(handler.baseFilename)
            break

    if not log_file or not log_file.exists():
        return

    file_size_kb = log_file.stat().st_size / 1024
    if file_size_kb < max_size_kb:
        return

    logger_key = logger.name
    if logger_key not in has_rotated_since_flap:
        has_rotated_since_flap[logger_key] = False
    if logger_key not in log_rotation_count:
        log_rotation_count[logger_key] = 0

    # Initialize secondary flag if not present
    if "flaps_detected_during" not in shared_flap_state:
        shared_flap_state["flaps_detected_during"] = False
    if "active_loggers" not in shared_flap_state:
        shared_flap_state["active_loggers"] = set()

    # Track this logger as active
    shared_flap_state["active_loggers"].add(logger_key)

    # Rotate with suffix if flaps detected, otherwise clear file
    if shared_flap_state.get("flaps_detected", False):
        # Flaps detected - rotate to new file to preserve data
        _rotate_to_new_file(
            log_file, logger, logger_key, log_rotation_count, keep_header, csv_header
        )
        has_rotated_since_flap[logger_key] = True

        # Check if all active loggers have rotated
        all_rotated = all(
            has_rotated_since_flap.get(log, False) for log in shared_flap_state["active_loggers"]
        )

        if all_rotated:
            # All loggers rotated - check if new flaps occurred during rotation
            if shared_flap_state.get("flaps_detected_during", False):
                # New flaps during rotation - keep cycling
                shared_flap_state["flaps_detected_during"] = False
                # Reset rotation flags for next cycle
                for log in shared_flap_state["active_loggers"]:
                    has_rotated_since_flap[log] = False
            else:
                # No new flaps - end rotation cycle
                shared_flap_state["flaps_detected"] = False
                for log in shared_flap_state["active_loggers"]:
                    has_rotated_since_flap[log] = False
    else:
        # No flaps - just clear the file and reuse it
        _clear_log_file(log_file, logger, keep_header, csv_header)
        # Reset rotation counter when clearing (start fresh)
        log_rotation_count[logger_key] = 0


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
