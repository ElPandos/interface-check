---
title:        Pydantic Models Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Pydantic Models Patterns

## Purpose
Define patterns for data validation and configuration management using Pydantic in the interface-check project.

## Core Patterns

### 1. BaseModel Configuration Pattern
Standard Pydantic model with custom configuration:

```python
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from typing import ClassVar

class Host(BaseModel):
    """Host configuration with secure password handling."""
    
    ip: str = ""
    username: str = ""
    password: SecretStr = SecretStr("")
    info: str = ""

    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_encoders={SecretStr: lambda v: v.get_secret_value()}
    )
```

**Benefits**: Type validation, JSON serialization, secure password handling.

### 2. Factory Method Pattern
Default value factories for common configurations:

```python
class Host(BaseModel):
    @classmethod
    def default_jump(cls) -> "Host":
        """Return default jump host configuration."""
        return cls(
            ip="137.58.231.134",
            username="emvekta",
            password=SecretStr("a"),
            info="Default value"
        )

    @classmethod
    def default_target(cls) -> "Host":
        """Return default target host configuration."""
        return cls(
            ip="172.16.180.1",
            username="hts",
            password=SecretStr("a"),
            info="Default value"
        )
```

### 3. Nested Model Pattern
Compose complex configurations from simpler models:

```python
class Route(BaseModel):
    """Connection path through multiple hosts."""
    
    summary: str
    target: Host
    jumps: list[Host] = Field(default_factory=list)

    @classmethod
    def default_route(cls) -> "Route":
        return cls(
            summary="137.58.231.134 ⟶ 172.16.180.1 (Target)",
            target=Host.default_target(),
            jumps=[Host.default_jump()],
        )

class Networks(BaseModel):
    """Networks configuration with hosts and connection paths."""
    
    hosts: list[Host] = Field(default_factory=lambda: [Host.default_jump(), Host.default_target()])
    routes: list[Route] = Field(default_factory=lambda: [Route.default_route()])
```

### 4. Enum Integration Pattern
Use enums for type-safe option values:

```python
from pydantic import BaseModel, ConfigDict
from typing import ClassVar

class Option(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(use_enum_values=True)

    name: str = ""
    type: Options = Options.SWITCH
    value: bool | int | str = False
    min: int | None = None
    max: int | None = None
```

### 5. Dataclass Configuration Pattern
Frozen dataclasses for immutable configuration:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ScanConfig:
    """Immutable application configuration for SLX/SUT scanning."""
    
    log_level: str
    log_rotation_timeout_sec: int
    
    jump_host: str
    jump_user: str
    jump_pass: str
    
    slx_host: str
    slx_scan_ports: list[str]
    slx_scan_interval_sec: int
    
    @classmethod
    def from_dict(cls, data: dict) -> "ScanConfig":
        """Create ScanConfig from nested JSON structure."""
        j, slx, sut = data["jump"], data["slx"], data["sut"]
        return cls(
            log_level=data.get("log_level", "info"),
            jump_host=j["host"],
            jump_user=j["user"],
            # ... more fields
        )
```

### 6. Validation Pattern
Comprehensive configuration validation:

```python
def validate(self, logger) -> bool:
    """Validate configuration values.
    
    Args:
        logger: Logger instance for error messages
        
    Returns:
        bool: True if valid, False otherwise
    """
    errors = []

    if self.log_rotation_timeout_sec <= 0:
        errors.append(f"Invalid log_rotation_timeout_sec: {self.log_rotation_timeout_sec} (must be > 0)")

    if not self.slx_scan_ports:
        errors.append("slx_scan_ports cannot be empty")

    if self.setup_protocol not in ["tcp", "udp"]:
        errors.append(f"Invalid protocol: {self.setup_protocol} (must be tcp or udp)")

    if errors:
        logger.error(f"{LogMsg.CONFIG_VALIDATION_FAILED.value}:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    logger.info(LogMsg.CONFIG_VALIDATION_SUCCESS.value)
    return True
```

### 7. Settings Aggregation Pattern
Combine multiple options into settings:

```python
class Settings(BaseModel):
    options: list[Option] = Field(
        default_factory=lambda: [
            Option.default_debug(),
            Option.default_dark(),
            Option.default_command(),
            Option.default_graph(),
            Option.default_refresh(),
        ]
    )

    def get_command_update_value(self) -> int:
        """Get command update value."""
        command_update = next(
            (s for s in self.options if s.name == Types.COMMAND.value), 
            None
        )
        if command_update is None:
            raise ValueError("UPDATE setting not defined")
        return int(command_update.value)
```

### 8. Root Configuration Pattern
Top-level configuration combining all settings:

```python
class Config(BaseModel):
    """Application configuration."""
    
    settings: Settings = Field(default_factory=Settings)
    networks: Networks = Field(default_factory=Networks)
```

## SecretStr Handling

### Secure Password Storage
```python
from pydantic import SecretStr

class Host(BaseModel):
    password: SecretStr = SecretStr("")
    
    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_encoders={SecretStr: lambda v: v.get_secret_value()}
    )

# Usage
host = Host(password=SecretStr("secret123"))
print(host.password)  # SecretStr('**********')
print(host.password.get_secret_value())  # 'secret123'
```

### JSON Serialization
```python
# Serialize with password exposed (for config files)
host.model_dump_json()  # Uses json_encoders

# Serialize with password hidden (for logging)
str(host.password)  # '**********'
```

## Field Patterns

### Default Factory
```python
class Networks(BaseModel):
    hosts: list[Host] = Field(default_factory=list)
    routes: list[Route] = Field(default_factory=lambda: [Route.default_route()])
```

### Optional Fields
```python
class Option(BaseModel):
    min: int | None = None
    max: int | None = None
```

### Constrained Values
```python
from pydantic import Field

class Config(BaseModel):
    port: int = Field(ge=1, le=65535, default=5001)
    timeout: int = Field(gt=0, default=30)
```

## Anti-Patterns to Avoid

### 1. Mutable Default Arguments
```python
# BAD
class Config(BaseModel):
    hosts: list[Host] = []

# GOOD
class Config(BaseModel):
    hosts: list[Host] = Field(default_factory=list)
```

### 2. Exposing Secrets in Logs
```python
# BAD
logger.info(f"Connecting with password: {host.password.get_secret_value()}")

# GOOD
logger.info(f"Connecting to {host.ip} as {host.username}")
```

### 3. Missing Validation
```python
# BAD
@classmethod
def from_dict(cls, data: dict) -> "Config":
    return cls(**data)

# GOOD
@classmethod
def from_dict(cls, data: dict) -> "Config":
    config = cls(**data)
    if not config.validate(logger):
        raise ValueError("Invalid configuration")
    return config
```

### 4. Hardcoded Defaults
```python
# BAD
class Host(BaseModel):
    ip: str = "192.168.1.1"

# GOOD
class Host(BaseModel):
    ip: str = ""
    
    @classmethod
    def default_jump(cls) -> "Host":
        return cls(ip="192.168.1.1", ...)
```

## Implementation Guidelines

### Model Organization
1. Define base models (Host, Option) first
2. Build composite models (Route, Settings) using base models
3. Create root Config model combining all settings
4. Add factory methods for common configurations

### Validation Strategy
1. Use Pydantic's built-in validators for type checking
2. Add custom `validate()` method for business rules
3. Log all validation errors with context
4. Return boolean for validation status

### Configuration Loading
```python
import json
from pathlib import Path

def load_config(path: Path) -> Config:
    """Load configuration from JSON file."""
    with path.open() as f:
        data = json.load(f)
    return Config.from_dict(data)
```

### Configuration Saving
```python
def save_config(config: Config, path: Path) -> None:
    """Save configuration to JSON file."""
    with path.open("w") as f:
        f.write(config.model_dump_json(indent=2))
```

## Version History

- v1.0 (2026-01-14 00:00:00): Initial Pydantic models patterns based on codebase analysis
