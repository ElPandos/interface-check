import logging
from pathlib import Path

from nicegui import ui

from src.models.configurations import AppConfig
from src.utils import system


class Configure:
    """Ensures the `~/.interface-check` folder and a default SSH config file."""

    # ---------------------------------------------------------------------------- #
    #                                 Default names                                #
    # ---------------------------------------------------------------------------- #

    _CONFIG_DIR = ".interface-check"

    _CONFIG_FILE = "ssh_config.json"
    _LOG_FILE = "main.log"

    # ---------------------------------------------------------------------------- #
    #                                     Paths                                    #
    # ---------------------------------------------------------------------------- #

    _HOME: Path = Path.home()
    _CONFIG_DIR: Path = _HOME / _CONFIG_DIR
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

        try:
            system.exist_file(self._CONFIG_FULL_PATH)
            logging.debug(f"Config found at: {self._CONFIG_FULL_PATH}")
        except FileNotFoundError:
            default_config = AppConfig().model_dump_json()
            system.save_json(default_config, self._CONFIG_FULL_PATH)
            logging.debug(f"Config file created at: {self._CONFIG_FULL_PATH}")

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
            system.save_json(cfg.model_dump_json(), self._CONFIG_FULL_PATH)
            ui.notify("Configuration saved", type="positive")
        except Exception as e:  # pragma: no cover
            ui.notify(f"Failed to save: {e}", type="negative")

    def load(self) -> AppConfig:
        """Load the JSON file and return a validated `AppConfig` instance."""
        data = system.load_json(self._CONFIG_FULL_PATH)
        return AppConfig().model_validate_json(data)
