"""Configuration management with improved independence."""

import json
import logging
from pathlib import Path
from typing import Any, TypeVar

from src.core.base import Component, Result, SimpleCache
from src.core.validation import ConfigValidator

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ConfigManager[T](Component):
    """Independent configuration manager."""

    def __init__(self, config_path: Path, validator: ConfigValidator | None = None):
        super().__init__("ConfigManager")
        self._config_path = config_path
        self._validator = validator or ConfigValidator()
        self._cache = SimpleCache[T]()
        self._config_data: T | None = None

    def _do_initialize(self) -> None:
        """Initialize configuration manager."""
        self._ensure_config_dir()

    def _do_cleanup(self) -> None:
        """Cleanup configuration manager."""
        self._cache.clear()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Result[T]:
        """Load configuration from file."""
        try:
            if not self._config_path.exists():
                return Result.fail("Configuration file not found")

            with open(self._config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Validate configuration
            validation_result = self._validator.validate(data)
            if not validation_result.success:
                return Result.fail(f"Invalid configuration: {validation_result.error}")

            self._config_data = data
            return Result.ok(data)

        except json.JSONDecodeError as e:
            return Result.fail(f"Invalid JSON: {e}")
        except Exception as e:
            return Result.fail(f"Failed to load config: {e}")

    def save(self, config: T) -> Result[None]:
        """Save configuration to file."""
        try:
            # Validate before saving
            if isinstance(config, dict):
                validation_result = self._validator.validate(config)
                if not validation_result.success:
                    return Result.fail(f"Invalid configuration: {validation_result.error}")

            self._ensure_config_dir()

            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._config_data = config
            return Result.ok(None)

        except Exception as e:
            return Result.fail(f"Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        if not isinstance(self._config_data, dict):
            return default
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> Result[None]:
        """Set configuration value."""
        if not isinstance(self._config_data, dict):
            return Result.fail("Configuration is not a dictionary")

        self._config_data[key] = value
        return self.save(self._config_data)

    @property
    def data(self) -> T | None:
        """Get current configuration data."""
        return self._config_data


class AppConfigManager(ConfigManager[dict[str, Any]]):
    """Application-specific configuration manager."""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = Path.home() / ".interface-check"

        config_path = config_dir / "config.json"
        validator = ConfigValidator(required_keys=["hosts", "system"])
        super().__init__(config_path, validator)

        self._default_config = {
            "hosts": [],
            "routes": [],
            "system": {
                "settings": [
                    {"name": "refresh_interval", "value": 5, "min": 1, "max": 60, "type": "slider"},
                    {"name": "command_timeout", "value": 30, "min": 5, "max": 300, "type": "slider"},
                    {"name": "debug_mode", "value": False, "type": "switch"},
                    {"name": "dark_mode", "value": False, "type": "switch"},
                ]
            },
        }

    def load_or_create_default(self) -> Result[dict[str, Any]]:
        """Load configuration or create default if not exists."""
        result = self.load()
        if not result.success:
            # Create default configuration
            save_result = self.save(self._default_config)
            if not save_result.success:
                return save_result
            return Result.ok(self._default_config)
        return result

    def get_hosts(self) -> list:
        """Get hosts configuration."""
        return self.get("hosts", [])

    def get_routes(self) -> list:
        """Get routes configuration."""
        return self.get("routes", [])

    def get_system_setting(self, name: str) -> Any:
        """Get system setting by name."""
        settings = self.get("system", {}).get("settings", [])
        for setting in settings:
            if setting.get("name") == name:
                return setting.get("value")
        return None
