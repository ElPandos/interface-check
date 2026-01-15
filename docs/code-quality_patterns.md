---
title:        Code Quality Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Code Quality Patterns

## Core Principles

1. **Single Responsibility**: Each module, class, and function should have one reason to change. When a component does too much, it becomes brittle and hard to test.

2. **Explicit Over Implicit**: Make dependencies, types, and behavior visible. Hidden state and magic methods create maintenance nightmares.

3. **Fail Fast, Fail Loud**: Validate inputs at boundaries, raise meaningful exceptions early. Silent failures propagate corruption.

4. **Composition Over Inheritance**: Favor small, composable units over deep inheritance hierarchies. Inheritance couples tightly; composition couples loosely.

5. **Immutability by Default**: Prefer immutable data structures. Mutation is a common source of bugs in concurrent and complex systems.

## Essential Patterns

### Type Safety Patterns

```python
# Pattern: Use strict typing with dataclasses/Pydantic
from dataclasses import dataclass
from typing import Final

@dataclass(frozen=True, slots=True)
class Host:
    """Immutable host configuration."""
    ip: str
    port: int = 22
    
    def __post_init__(self) -> None:
        if not self.ip:
            raise ValueError("IP address required")

# Pattern: Result types for operations that can fail
from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

@dataclass(frozen=True)
class Result(Generic[T, E]):
    value: T | None = None
    error: E | None = None
    
    @property
    def is_ok(self) -> bool:
        return self.error is None
    
    @classmethod
    def ok(cls, value: T) -> "Result[T, E]":
        return cls(value=value)
    
    @classmethod
    def fail(cls, error: E) -> "Result[T, E]":
        return cls(error=error)
```

### Resource Management Patterns

```python
# Pattern: Context managers for resource lifecycle
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def managed_connection(host: str) -> Iterator[Connection]:
    """Ensure connection cleanup regardless of exceptions."""
    conn = Connection(host)
    try:
        conn.connect()
        yield conn
    finally:
        conn.disconnect()

# Pattern: Dependency injection for testability
class Scanner:
    def __init__(self, connection_factory: Callable[[], Connection]) -> None:
        self._connection_factory = connection_factory
    
    def scan(self) -> list[Result]:
        with self._connection_factory() as conn:
            return conn.execute("scan")
```

### Error Handling Patterns

```python
# Pattern: Domain-specific exceptions with context
class NetworkError(Exception):
    """Base for network-related errors."""
    def __init__(self, message: str, host: str, cause: Exception | None = None):
        super().__init__(message)
        self.host = host
        self.cause = cause

# Pattern: Structured logging with context
import logging
from typing import Any

def log_operation(
    logger: logging.Logger,
    operation: str,
    **context: Any
) -> None:
    logger.info(
        "%s completed",
        operation,
        extra={"operation": operation, **context}
    )
```

### Validation Patterns

```python
# Pattern: Validate at boundaries, trust internally
from pydantic import BaseModel, field_validator

class ConfigInput(BaseModel):
    """External input - validate everything."""
    host: str
    port: int
    
    @field_validator("port")
    @classmethod
    def port_in_range(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be 1-65535")
        return v

# Internal code trusts validated data
def connect(config: ConfigInput) -> Connection:
    # No re-validation needed - ConfigInput guarantees validity
    return Connection(config.host, config.port)
```

### Separation of Concerns

```python
# Pattern: Pure functions for logic, impure for I/O
def calculate_metrics(data: list[float]) -> dict[str, float]:
    """Pure function - no side effects, easily testable."""
    return {
        "mean": sum(data) / len(data) if data else 0.0,
        "max": max(data) if data else 0.0,
    }

async def fetch_and_process(client: HttpClient) -> dict[str, float]:
    """Impure function - handles I/O, delegates logic."""
    data = await client.fetch("/metrics")
    return calculate_metrics(data)
```

## Anti-Patterns to Avoid

### God Objects
```python
# BAD: Class does everything
class Application:
    def connect(self): ...
    def parse_config(self): ...
    def render_ui(self): ...
    def send_email(self): ...
    def query_database(self): ...

# GOOD: Single responsibility per class
class ConnectionManager: ...
class ConfigParser: ...
class UIRenderer: ...
```

### Primitive Obsession
```python
# BAD: Raw strings everywhere
def connect(host: str, user: str, password: str): ...

# GOOD: Domain types
@dataclass(frozen=True)
class Credentials:
    username: str
    password: SecretStr

def connect(host: Host, credentials: Credentials): ...
```

### Stringly Typed Code
```python
# BAD: Magic strings
if status == "connected": ...
if log_level == "debug": ...

# GOOD: Enums
class Status(Enum):
    CONNECTED = auto()
    DISCONNECTED = auto()

if status == Status.CONNECTED: ...
```

### Mutable Default Arguments
```python
# BAD: Mutable default
def append_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)  # Shared across calls!
    return items

# GOOD: None sentinel
def append_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

### Bare Except Clauses
```python
# BAD: Catches everything including KeyboardInterrupt
try:
    risky_operation()
except:
    pass

# GOOD: Specific exceptions with logging
try:
    risky_operation()
except ConnectionError as e:
    logger.exception("Connection failed: %s", e)
    raise
```

### Deep Nesting
```python
# BAD: Arrow code
def process(data):
    if data:
        if data.valid:
            if data.ready:
                return data.value

# GOOD: Early returns (guard clauses)
def process(data):
    if not data:
        return None
    if not data.valid:
        return None
    if not data.ready:
        return None
    return data.value
```

### Boolean Blindness
```python
# BAD: What does True mean?
def connect(host: str, secure: bool, verify: bool): ...
connect("host", True, False)  # Unclear

# GOOD: Named parameters or enums
class SecurityMode(Enum):
    NONE = auto()
    TLS = auto()
    TLS_VERIFIED = auto()

def connect(host: str, security: SecurityMode): ...
connect("host", SecurityMode.TLS)
```

## Implementation Guidelines

### 1. Project Setup
```bash
# pyproject.toml essentials
[tool.ruff]
line-length = 88
target-version = "py312"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "RUF"]

[tool.mypy]
strict = true
warn_return_any = true
```

### 2. Code Organization
```
src/
├── core/           # Business logic (pure, testable)
├── interfaces/     # Abstract protocols/ABCs
├── adapters/       # External system integrations
├── models/         # Data structures (Pydantic/dataclasses)
└── ui/             # Presentation layer
```

### 3. Testing Strategy
- Unit tests for pure functions (fast, isolated)
- Integration tests for adapters (with mocks/fakes)
- End-to-end tests for critical paths (minimal)

### 4. Review Checklist
- [ ] Types complete and strict
- [ ] No bare exceptions
- [ ] Resources properly managed (context managers)
- [ ] No mutable default arguments
- [ ] Single responsibility per function/class
- [ ] Meaningful names (no `data`, `info`, `manager` without context)

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Type Coverage | 100% | `mypy --strict` passes |
| Lint Errors | 0 | `ruff check` clean |
| Cyclomatic Complexity | ≤10 per function | `radon cc -a` |
| Test Coverage | ≥80% | `pytest --cov` |
| Duplicate Code | <3% | `ruff` or `pylint` |
| Doc Coverage | Public APIs | All public functions documented |

### Quality Gates
1. **Pre-commit**: Format (ruff), lint, type-check
2. **CI Pipeline**: Full test suite, coverage threshold
3. **Code Review**: Architecture alignment, pattern adherence

## Sources & References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) — Official Python style guide
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/) — Type annotation specification
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) — Comprehensive style guide
- [Ruff Documentation](https://docs.astral.sh/ruff/) — Fast Python linter
- [mypy Documentation](https://mypy.readthedocs.io/) — Static type checker
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/) — Data validation library
- [Clean Code by Robert C. Martin](https://www.oreilly.com/library/view/clean-code-a/9780136083238/) — Foundational patterns
- [Effective Python by Brett Slatkin](https://effectivepython.com/) — Python-specific best practices

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version with core patterns, anti-patterns, and implementation guidelines
