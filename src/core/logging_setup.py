"""Centralized logging configuration for eye scan application."""

import json
import logging
from pathlib import Path
import sys

from src.core.logging import create_formatter
from src.platform.enums.log import LogName


def get_log_directory() -> Path:
    """Get or create log directory with timestamp.

    Returns:
        Path: Log directory path
    """
    from datetime import datetime as dt

    log_time_stamp = f"{dt.now().strftime('%Y%m%d_%H%M%S')}"
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).parent / "logs"
    else:
        log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamped_dir = log_dir / log_time_stamp
    timestamped_dir.mkdir(exist_ok=True)
    return timestamped_dir


def get_log_level() -> int:
    """Load log level from config file.

    Returns:
        int: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        if getattr(sys, "frozen", False):
            config_file = Path(sys.executable).parent / "main_eye_cfg.json"
        else:
            config_file = Path(__file__).parent.parent.parent / "main_eye_cfg.json"
        with config_file.open() as f:
            config_data = json.load(f)
        log_level_str = config_data.get("log_level", "info").upper()
        return getattr(logging, log_level_str, logging.INFO)
    except Exception:
        return logging.INFO


def setup_root_logger(log_dir: Path, log_level: int) -> tuple[Path, Path]:
    """Configure root logger with file and console handlers.

    Args:
        log_dir: Directory for log files
        log_level: Logging level

    Returns:
        tuple[Path, Path]: Paths to main and memory log files
    """
    main_log = log_dir / "main.log"
    memory_log = log_dir / "memory.log"

    root_file_handler = logging.FileHandler(main_log)
    root_file_handler.setFormatter(create_formatter(LogName.MAIN.value))
    root_console_handler = logging.StreamHandler()
    root_console_handler.setFormatter(create_formatter(LogName.MAIN.value))

    logging.basicConfig(
        level=log_level,
        handlers=[root_file_handler, root_console_handler],
    )

    return main_log, memory_log


def setup_component_loggers(log_dir: Path, log_level: int) -> dict[str, logging.Logger]:
    """Configure component-specific loggers.

    Each logger writes to its own file and propagates to root logger (main.log).

    Args:
        log_dir: Directory for log files
        log_level: Logging level

    Returns:
        dict[str, logging.Logger]: Dictionary of configured loggers
    """
    logger_configs = [
        (LogName.MAIN, None),
        (LogName.MEMORY, "memory.log"),
        (LogName.SUT_SYSTEM_INFO, "sut_system_info.log"),
        (LogName.SUT_MXLINK, "sut_mxlink.log"),
        (LogName.SUT_MTEMP, "sut_mtemp.log"),
        (LogName.SUT_LINK_FLAP, "sut_link_flap.log"),
        (LogName.SLX_EYE, "slx_eye.log"),
    ]

    loggers = {}
    for logger_enum, log_file in logger_configs:
        logger = logging.getLogger(logger_enum.value)
        logger.setLevel(log_level)

        if log_file:
            logger.propagate = False
            handler = logging.FileHandler(log_dir / log_file)
            handler.setFormatter(create_formatter(logger_enum.value))
            logger.addHandler(handler)
        else:
            logger.propagate = True

        loggers[logger_enum] = logger

    return loggers


def initialize_logging() -> dict[str, logging.Logger]:
    """Initialize complete logging system.

    Sets up root logger, component loggers, and returns logger references.

    Returns:
        dict[str, logging.Logger]: Dictionary with keys:
            - main, memory, sut_system_info, sut_mxlink, sut_mtemp, sut_link_flap, slx_eye
    """
    log_dir = get_log_directory()
    log_level = get_log_level()

    setup_root_logger(log_dir, log_level)
    loggers = setup_component_loggers(log_dir, log_level)

    return {
        "main": loggers[LogName.MAIN],
        "memory": loggers[LogName.MEMORY],
        "sut_system_info": loggers[LogName.SUT_SYSTEM_INFO],
        "sut_mxlink": loggers[LogName.SUT_MXLINK],
        "sut_mtemp": loggers[LogName.SUT_MTEMP],
        "sut_link_flap": loggers[LogName.SUT_LINK_FLAP],
        "slx_eye": loggers[LogName.SLX_EYE],
    }
