import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nicegui import ui

from src.models.config import Config
from src.platform import platform
from src.platform.enums.log import LogName
from src.platform.platform import create_dir

logger = logging.getLogger(LogName.CORE_MAIN.value)


class Configure:
    """Configuration and logging manager.

    Manages application configuration files and logging setup.
    """

    _cfg_DIR = Path.home() / ".interface-check"
    _cfg_FILE = _cfg_DIR / "ssh_cfg.json"
    _LOG_FILE = _cfg_DIR / "main.log"
    _NOISY_LOGGERS = ("paramiko", "asyncio", "matplotlib")

    _initialized = False

    def __init__(self) -> None:
        """Initialize configuration manager.

        Creates config directory and default config if missing.
        """
        if not self._initialized:
            self._setup()
            Configure._initialized = True

    def _setup(self) -> None:
        """Initialize directory and create default config if missing.

        Creates config directory and generates default config.json.
        """
        create_dir(self._cfg_DIR)

        if not self._cfg_FILE.exists():
            platform.save_json(Config().model_dump(), self._cfg_FILE)
            logger.debug(f"Config created: {self._cfg_FILE}")

    # ---------------------------------------------------------------------------- #
    #                                  Public API                                  #
    # ---------------------------------------------------------------------------- #

    @property
    def config_path(self) -> Path:
        """Get config file path.

        Returns:
            Path to configuration file
        """
        return self._cfg_FILE

    @property
    def log_path(self) -> Path:
        """Get log file path.

        Returns:
            Path to log file
        """
        return self._LOG_FILE

    def save(self, cfg: Config) -> None:
        """Save config to file with UI notification.

        Args:
            cfg: Configuration object to save
        """
        try:
            platform.save_json(cfg.model_dump(), self._cfg_FILE)
            ui.notify("Configuration saved", type="positive")
        except Exception as e:
            ui.notify(f"Save failed: {e}", type="negative")
            logger.exception("Config save error")

    def load(self, external: dict | None = None) -> Config:
        """Load config from file or external dict.

        Args:
            external: Optional external config dict

        Returns:
            Loaded or default Config object
        """
        if external:
            return Config.model_validate(external)

        try:
            data = platform.load_json(self._cfg_FILE)
            return Config.model_validate(data)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Config issue: {e}. Using defaults.")
            default = Config()
            self.save(default)
            return default

    def setup_logging(self, level: int = logging.INFO) -> None:
        """Setup logging with file rotation and console output.

        Args:
            level: Logging level (default: INFO)
        """
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s [%(name)-30s.%(funcName)s():%(lineno)d]: %(message)s"
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
    """Setup logging convenience wrapper.

    Args:
        level: Logging level (default: INFO)
    """
    Configure().setup_logging(level)
