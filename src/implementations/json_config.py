"""JSON-based configuration implementation."""

import json
import logging
from pathlib import Path
from typing import Any

from src.interfaces.configuration import IConfigurationFactory, IConfigurationProvider

logger = logging.getLogger(__name__)


class JsonConfigurationProvider(IConfigurationProvider):
    """JSON file-based configuration provider."""

    def __init__(self, config_path: Path):
        self._config_path = config_path
        self._data: dict[str, Any] = {}
        self._load_config()

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split(".")
        value = self._data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split(".")
        data = self._data

        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]

        data[keys[-1]] = value

    def save(self) -> None:
        """Persist configuration to file."""
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w") as f:
                json.dump(self._data, f, indent=2, default=str)
            logger.debug(f"Configuration saved to {self._config_path}")
        except Exception:
            logger.exception(f"Failed to save configuration to {self._config_path}")

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def get_section(self, section: str) -> dict[str, Any]:
        """Get entire configuration section."""
        return self.get(section, {})

    def _load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self._config_path.exists():
                with open(self._config_path) as f:
                    self._data = json.load(f)
                logger.debug(f"Configuration loaded from {self._config_path}")
            else:
                self._data = {}
                logger.debug(f"Configuration file not found: {self._config_path}")
        except Exception:
            logger.exception(f"Failed to load configuration from {self._config_path}")
            self._data = {}


class JsonConfigurationFactory(IConfigurationFactory):
    """Factory for creating JSON configuration providers."""

    def create_provider(self, source: str) -> IConfigurationProvider:
        """Create JSON configuration provider from file path."""
        return JsonConfigurationProvider(Path(source))
