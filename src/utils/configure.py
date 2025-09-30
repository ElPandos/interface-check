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

    # ---------------------------------------------------------------------------- #
    #                                     Paths                                    #
    # ---------------------------------------------------------------------------- #

    _HOME: Path = Path.home()
    _CONFIG_DIR: Path = _HOME / _CONFIG_DIR
    _FULL_PATH: Path = _CONFIG_DIR / _CONFIG_FILE

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
            system.exist_file(self._FULL_PATH)
            #logger.debug(f"Config found at: {self._FULL_PATH}")
        except FileNotFoundError:
            default_config = AppConfig().model_dump_json()
            system.save_json(default_config, self._FULL_PATH)
            logger.debug(f"Config file created at: {self._FULL_PATH}")

    # ---------------------------------------------------------------------------- #
    #                                  Public API                                  #
    # ---------------------------------------------------------------------------- #

    def get_full_path(self) -> Path:
        """Return the full path to the config file (creates defaults if needed)."""
        self._setup()
        return self._FULL_PATH

    def save(self, cfg: AppConfig) -> None:
        """Persist *cfg* to the JSON file."""
        try:
            system.save_json(cfg.model_dump_json(), self._FULL_PATH)
            ui.notify("Configuration saved", type="positive")
        except Exception as exc:          # pragma: no cover
            ui.notify(f"Failed to save: {exc}", type="negative")

    def load(self) -> AppConfig:
        """Load the JSON file and return a validated `AppConfig` instance."""
        data = system.load_json(self._FULL_PATH)
        return AppConfig().model_validate_json(data)

