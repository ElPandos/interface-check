import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nicegui import ui

from src.models.config import Config
from src.platform import platform
from src.platform.platform import create_dir

logger = logging.getLogger(__name__)


class Configure:
    """Manages configuration and logging setup."""

    _CONFIG_DIR = Path.home() / ".interface-check"
    _CONFIG_FILE = _CONFIG_DIR / "ssh_config.json"
    _LOG_FILE = _CONFIG_DIR / "main.log"
    _NOISY_LOGGERS = ("paramiko", "asyncio", "matplotlib")

    _initialized = False

    def __init__(self) -> None:
        if not self._initialized:
            self._setup()
            Configure._initialized = True

    def _setup(self) -> None:
        """Initialize directory and default config."""
        create_dir(self._CONFIG_DIR)

        if not self._CONFIG_FILE.exists():
            platform.save_json(Config().model_dump(), self._CONFIG_FILE)
            logger.debug(f"Config created: {self._CONFIG_FILE}")

    # ---------------------------------------------------------------------------- #
    #                                  Public API                                  #
    # ---------------------------------------------------------------------------- #

    @property
    def config_path(self) -> Path:
        return self._CONFIG_FILE

    @property
    def log_path(self) -> Path:
        return self._LOG_FILE

    def save(self, config: Config) -> None:
        """Save configuration to file."""
        try:
            platform.save_json(config.model_dump(), self._CONFIG_FILE)
            ui.notify("Configuration saved", type="positive")
        except Exception as e:
            ui.notify(f"Save failed: {e}", type="negative")
            logger.exception("Config save error")

    def load(self, external: dict | None = None) -> Config:
        """Load and validate configuration."""
        if external:
            return Config.model_validate(external)

        try:
            data = platform.load_json(self._CONFIG_FILE)
            return Config.model_validate(data)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Config issue: {e}. Using defaults.")
            default = Config()
            self.save(default)
            return default

    def setup_logging(self, level: int = logging.INFO) -> None:
        """Configure rotating file and console logging."""
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s():%(lineno)d]: %(message)s"
        )

        handlers = [
            RotatingFileHandler(
                self._LOG_FILE, maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"
            ),
            logging.StreamHandler(),
        ]

        for handler in handlers:
            handler.setFormatter(formatter)

        root = logging.getLogger()
        root.setLevel(level)
        root.handlers.clear()
        root.handlers.extend(handlers)

        # Suppress noisy loggers
        for name in self._NOISY_LOGGERS:
            logging.getLogger(name).setLevel(logging.WARNING)

        logger.debug(f"Logging initialized: {logging.getLevelName(level)}")


def setup_logging(level: int = logging.INFO) -> None:
    """Convenience function for setting up logging."""
    Configure().setup_logging(level)
