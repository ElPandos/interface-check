import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nicegui import ui

logger = logging.getLogger(__name__)

from src.models.configurations import AppConfig
from src.utils import system


class Configure:
    """Ensures the `~/.interface-check` folder and a default SSH config file."""

    # ---------------------------------------------------------------------------- #
    #                                 Default names                                #
    # ---------------------------------------------------------------------------- #

    _CONFIG_DIR_NAME = ".interface-check"
    _CONFIG_FILE = "ssh_config.json"
    _LOG_FILE = "main.log"

    # ---------------------------------------------------------------------------- #
    #                                     Paths                                    #
    # ---------------------------------------------------------------------------- #

    _HOME: Path = Path.home()
    _CONFIG_DIR: Path = _HOME / _CONFIG_DIR_NAME
    _CONFIG_FULL_PATH: Path = _CONFIG_DIR / _CONFIG_FILE
    _LOG_FULL_PATH: Path = _CONFIG_DIR / _LOG_FILE

    # ---------------------------------------------------------------------------- #
    #                                  Constructor                                 #
    # ---------------------------------------------------------------------------- #

    def __init__(self) -> None:
        self._setup()

    # ---------------------------------------------------------------------------- #
    #                                    Helpers                                   #
    # ---------------------------------------------------------------------------- #

    def _ensure_dir(self) -> None:
        """Create `~/.interface-check` if it does not exist."""
        system.create_dir(self._CONFIG_DIR)

    def _setup(self) -> None:
        """
        Write the default config file if it is missing.
        """
        self._ensure_dir()

        if not self._CONFIG_FULL_PATH.exists():
            default_config = AppConfig().model_dump()
            system.save_json(default_config, self._CONFIG_FULL_PATH)
            logger.debug(f"Config file created at: {self._CONFIG_FULL_PATH}")
        else:
            logger.debug(f"Config found at: {self._CONFIG_FULL_PATH}")

    # ---------------------------------------------------------------------------- #
    #                                  Public API                                  #
    # ---------------------------------------------------------------------------- #

    def get_log_full_path(self) -> Path:
        """Return the full path to the config file (creates defaults if needed)."""
        self._setup()
        return self._LOG_FULL_PATH

    def get_config_full_path(self) -> Path:
        """Return the full path to the config file (creates defaults if needed)."""
        self._setup()
        return self._CONFIG_FULL_PATH

    def save(self, cfg: AppConfig) -> None:
        """Persist *cfg* to the JSON file."""
        try:
            system.save_json(cfg.model_dump(), self._CONFIG_FULL_PATH)
            ui.notify("Configuration saved", type="positive")
        except Exception as e:
            ui.notify(f"Failed to save: {e}", type="negative")

    def load(self) -> AppConfig:
        """Load the JSON file and return a validated `AppConfig` instance."""
        try:
            data = system.load_json(self._CONFIG_FULL_PATH)
            return AppConfig.model_validate(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Config file issue: {e}. Creating default config.")
            default_config = AppConfig()
            self.save(default_config)
            return default_config

    def setup_logging(self, level: int = logging.INFO) -> None:
        """
        Configure application-wide logging with:
          - Console output (StreamHandler)
          - Rotating file logs (RotatingFileHandler)
        Automatically limits log file size and keeps backup history.

        Parameters
        ----------
        level : int
            Logging level (e.g., logging.DEBUG, logging.INFO, logging.ERROR)
        """
        # -------------------------- Determine log file path ------------------------- #
        log_full_path = self.get_log_full_path()

        # --------------------- Define format and rotation policy -------------------- #

        # Rotate after 5 MB, keep last 5 backups (configurable)
        file_handler = RotatingFileHandler(
            filename=log_full_path,
            maxBytes=20 * 1024 * 1024,  # 5 MB
            backupCount=10,  # keep all rotated files
            encoding="utf-8",
        )
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # ---------------------- Attach handlers to root logger ---------------------- #
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # ----- Optional: suppress overly chatty loggers (like paramiko, asyncio) ---- #
        for noisy in ("paramiko", "asyncio", "matplotlib"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

        root_logger.debug(f"Logging initialized at level {logging.getLevelName(level)}")


def setup_logging(level: int = logging.INFO) -> None:
    """Convenience function for setting up logging."""
    Configure().setup_logging(level)
