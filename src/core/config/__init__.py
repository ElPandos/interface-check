"""Configuration loading utilities for main scripts.

Provides shared config loading logic with PyInstaller support.
"""

import json
import logging
from pathlib import Path
import sys
from typing import TypeVar

from src.core.config.scan import ScanConfig
from src.core.config.traffic import TrafficConfig
from src.core.enum.messages import LogMsg

T = TypeVar("T")


def load_config_file(config_filename: str, config_class: type[T], logger: logging.Logger) -> T:
    """Load configuration from JSON file with PyInstaller support.

    Args:
        config_filename: Name of config file (e.g., "main_scan_cfg.json")
        config_class: Config class with from_dict() classmethod
        logger: Logger instance for error reporting

    Returns:
        Loaded configuration instance

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file has invalid JSON
    """
    # Handle PyInstaller bundled executable
    if getattr(sys, "frozen", False):
        config_file = Path(sys.executable).parent / config_filename
    else:
        config_file = Path.cwd() / config_filename

    try:
        with config_file.open() as f:
            data = json.load(f)
        logger.info(LogMsg.CONFIG_LOADED.value)
        return config_class.from_dict(data)
    except FileNotFoundError:
        logger.exception(f"{LogMsg.MAIN_CONFIG_NOT_FOUND.value}: {config_file}")
        logger.exception(LogMsg.MAIN_CONFIG_SAME_DIR.value)
        raise
    except json.JSONDecodeError:
        logger.exception(LogMsg.MAIN_CONFIG_INVALID_JSON.value)
        raise


def load_scan_config(logger: logging.Logger) -> ScanConfig:
    """Load scan configuration from main_scan_cfg.json.

    Args:
        logger: Logger instance for error reporting

    Returns:
        ScanConfig: Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file has invalid JSON
    """
    logger.debug(LogMsg.CONFIG_START)
    cfg = load_config_file("main_scan_cfg.json", ScanConfig, logger)
    logger.info(LogMsg.CONFIG_LOADED.value)
    return cfg


def load_traffic_config(logger: logging.Logger) -> TrafficConfig:
    """Load traffic configuration from main_scan_traffic_cfg.json.

    Args:
        logger: Logger instance for error reporting

    Returns:
        TrafficConfig: Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file has invalid JSON
    """
    return load_config_file("main_scan_traffic_cfg.json", TrafficConfig, logger)
