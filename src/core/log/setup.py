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


def get_log_level(config_file: str | None = None) -> int:
    """Load log level from config file.

    Args:
        config_file: Optional config file name (default: main_scan_cfg.json)

    Returns:
        int: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        if config_file is None:
            config_file = "main_scan_cfg.json"
        
        if getattr(sys, "frozen", False):
            config_path = Path(sys.executable).parent / config_file
        else:
            config_path = Path(__file__).parent.parent.parent.parent / config_file

        if not config_path.exists():
            print(f"Config file not found: {config_path}", file=sys.stderr)
            return logging.INFO

        with config_path.open() as f:
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
    logger_configs = [(LogName.MAIN, None)] + [
        (log, f"{log.value}.log") for log in LogName if log != LogName.MAIN
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


def init_logging(config_file: str | None = None) -> dict[str, logging.Logger | Path]:
    """Initialize complete logging system.

    Args:
        config_file: Optional config file name (default: main_scan_cfg.json)

    Returns:
        dict[str, logging.Logger | Path]: Dictionary with keys:
            - main, memory, sut_system_info, sut_mxlink, sut_mtemp, sut_link_flap, slx_eye
            - log_dir: Path to log directory
    """
    log_dir = get_log_directory()
    log_level = get_log_level(config_file)

    setup_root_logger(log_dir, log_level)
    loggers = setup_component_loggers(log_dir, log_level)

    return {log.value: logger for log, logger in loggers.items()} | {"log_dir": log_dir}
