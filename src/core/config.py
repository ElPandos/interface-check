import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nicegui import ui

from src.core.enum.messages import LogMsg
from src.core.log.formatter import create_formatter
from src.models.config import Config
from src.platform import platform
from src.platform.enums.log import LogName
from src.platform.platform import create_dir

logger = logging.getLogger(LogName.MAIN.value)


class Configure:
    """Configuration and logging manager.

    Manages application configuration files and logging setup.
    """

    _cfg_dir = Path.home() / ".interface-check"
    _cfg_file = _cfg_dir / "ssh_cfg.json"
    _log_file = _cfg_dir / "main.log"
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

        if not self._cfg_file.exists():
            platform.save_json(Config().model_dump(), self._cfg_file)
            logger.debug(f"{LogMsg.CONFIG_CREATED.value}: {self._cfg_file}")

    # ---------------------------------------------------------------------------- #
    #                                  Public API                                  #
    # ---------------------------------------------------------------------------- #

    @property
    def config_path(self) -> Path:
        """Get config file path.

        Returns:
            Path to configuration file
        """
        return self._cfg_file

    @property
    def log_path(self) -> Path:
        """Get log file path.

        Returns:
            Path to log file
        """
        return self._log_file

    def save(self, cfg: Config) -> None:
        """Save config to file with UI notification.

        Args:
            cfg: Configuration object to save
        """
        try:
            platform.save_json(cfg.model_dump(), self._cfg_file)
            ui.notify(LogMsg.CONFIG_LOADED.value, type="positive")
        except Exception as e:
            ui.notify(f"{LogMsg.CONFIG_FAILED.value}: {e}", type="negative")
            logger.exception(LogMsg.CONFIG_FAILED.value)

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
            data = platform.load_json(self._cfg_file)
            return Config.model_validate(data)
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"{LogMsg.CONFIG_FAILED.value}: {e}")
            default = Config()
            self.save(default)
            return default

    def setup_logging(self, level: int = logging.INFO) -> None:
        """Setup logging with file rotation and console output.

        Args:
            level: Logging level (default: INFO)
        """
        formatter = create_formatter("config")

        handlers = [
            RotatingFileHandler(self._log_file, maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"),
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

        logger.debug(f"{LogMsg.CONFIG_START.value}: {logging.getLevelName(level)}")


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging convenience wrapper.

    Args:
        level: Logging level (default: INFO)
    """
    Configure().setup_logging(level)
