"""Centralized logging configuration for eye scan application."""

from datetime import datetime as dt
import json
import logging
from pathlib import Path
import sys

from src.core.log.formatter import create_formatter
from src.platform.enums.log import LogName


def get_log_directory() -> Path:
    """Get or create log directory with timestamp.

    Returns:
        Path: Log directory path
    """
    log_time_stamp = f"{dt.now().strftime('%Y%m%d_%H%M%S')}"
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).parent / "logs"
    else:
        log_dir = Path(__file__).parent.parent.parent.parent / "logs"
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
            config_file = Path(sys.executable).parent / "main_scan_cfg.json"
        else:
            config_file = Path(__file__).parent.parent.parent.parent / "main_scan_cfg.json"

        if not config_file.exists():
            print(f"Config file not found: {config_file}", file=sys.stderr)
            return logging.INFO

        with config_file.open() as f:
            config_data = json.load(f)
        log_level_str = config_data.get("log_level", "info").upper()
        level = getattr(logging, log_level_str, logging.INFO)
        print(f"Log level set to: {log_level_str} ({level})", file=sys.stderr)
        return level
    except Exception as e:
        print(f"Error loading log level: {e}", file=sys.stderr)
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
        (LogName.MEMORY, f"{LogName.MEMORY.value}.log"),
        (LogName.SUT_SYSTEM_INFO, f"{LogName.SUT_SYSTEM_INFO.value}.log"),
        (LogName.SUT_MXLINK, f"{LogName.SUT_MXLINK.value}.log"),
        (LogName.SUT_MXLINK_AMBER, f"{LogName.SUT_MXLINK_AMBER.value}.log"),
        (LogName.SUT_MTEMP, f"{LogName.SUT_MTEMP.value}.log"),
        (LogName.SUT_ETHTOOL, f"{LogName.SUT_ETHTOOL.value}.log"),
        (LogName.SUT_LINK_FLAP, f"{LogName.SUT_LINK_FLAP.value}.log"),
        (LogName.SLX_EYE, f"{LogName.SLX_EYE.value}.log"),
        (LogName.SLX_DSC, f"{LogName.SLX_DSC.value}.log"),
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


def initialize_logging() -> dict[str, logging.Logger | Path]:
    """Initialize complete logging system.

    Sets up root logger, component loggers, and returns logger references.

    Returns:
        dict[str, logging.Logger | Path]: Dictionary with keys:
            - main, memory, sut_system_info, sut_mxlink, sut_mtemp, sut_link_flap, slx_eye
            - log_dir: Path to log directory
    """
    log_dir = get_log_directory()
    log_level = get_log_level()

    setup_root_logger(log_dir, log_level)
    loggers = setup_component_loggers(log_dir, log_level)

    return {
        LogName.MAIN.value: loggers[LogName.MAIN],
        LogName.MEMORY.value: loggers[LogName.MEMORY],
        LogName.SUT_SYSTEM_INFO.value: loggers[LogName.SUT_SYSTEM_INFO],
        LogName.SUT_MXLINK.value: loggers[LogName.SUT_MXLINK],
        LogName.SUT_MXLINK_AMBER.value: loggers[LogName.SUT_MXLINK_AMBER],
        LogName.SUT_MTEMP.value: loggers[LogName.SUT_MTEMP],
        LogName.SUT_ETHTOOL.value: loggers[LogName.SUT_ETHTOOL],
        LogName.SUT_LINK_FLAP.value: loggers[LogName.SUT_LINK_FLAP],
        LogName.SLX_EYE.value: loggers[LogName.SLX_EYE],
        LogName.SLX_DSC.value: loggers[LogName.SLX_DSC],
        "log_dir": log_dir,
    }
