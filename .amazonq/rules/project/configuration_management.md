# Configuration Management

## Configuration Structure
- **JSON-based**: Primary config in `config/config.json`
- **Pydantic models**: Type-safe configuration classes
- **Environment variables**: Loaded via `python-dotenv`
- **Validation**: Automatic validation on load

## Configuration Models
```python
from pydantic import BaseModel, SecretStr
from typing import List

@dataclass(frozen=True)
class HostConfig:
    ip: str
    username: str
    password: SecretStr
    jump: bool = False
    remote: bool = False

@dataclass(frozen=True)
class AppConfig:
    hosts: List[HostConfig]
    settings: dict[str, Any]
```

## Configuration Loading
```python
class Configure:
    def load(self) -> AppConfig:
        try:
            with open("config/config.json") as f:
                data = json.load(f)
            return AppConfig.model_validate(data)
        except (FileNotFoundError, ValidationError) as e:
            logger.exception("Configuration loading failed")
            raise ConfigurationError from e
```

## Security Considerations
- **Secrets**: Use `SecretStr` for passwords
- **File permissions**: Restrict config file access
- **Environment isolation**: Separate dev/prod configs
- **Validation**: Strict validation of all inputs

## Configuration Updates
- **Runtime changes**: Update config and save to file
- **UI integration**: Settings panel for user modifications
- **Backup**: Keep backup of working configurations
- **Migration**: Handle config schema changes gracefully