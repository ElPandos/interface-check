---
title:        Development Standards Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Development Standards Patterns

## Core Principles

1. **Consistency Over Cleverness**: Uniform code style across the codebase reduces cognitive load. A mediocre pattern applied consistently beats brilliant patterns applied sporadically.

2. **Explicit Over Implicit**: Type hints, clear naming, and documented contracts prevent bugs and ease onboarding. Magic behavior creates maintenance nightmares.

3. **Fail Fast, Fail Loud**: Validate inputs at boundaries, raise exceptions early, log failures with context. Silent failures compound into catastrophic debugging sessions.

4. **Single Responsibility**: Each module, class, and function should have one reason to change. Cohesion within, loose coupling between.

5. **Automate Standards Enforcement**: Linters, formatters, and CI checks remove human judgment from style debates. If it's not automated, it's not enforced.

## Essential Patterns

### Code Organization

**Layered Architecture**
```
src/
├── core/           # Business logic, no I/O dependencies
├── interfaces/     # Abstract contracts (protocols/ABCs)
├── adapters/       # External integrations (DB, API, SSH)
├── models/         # Data structures (Pydantic, dataclasses)
└── ui/             # Presentation layer
```

**Module Boundaries**
- Public API via `__all__` exports
- Internal modules prefixed with `_`
- Circular imports indicate design flaws—refactor immediately

### Type Safety

**Strict Typing Pattern**
```python
from typing import Protocol, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")

class Repository(Protocol[T]):
    def get(self, id: str) -> T | None: ...
    def save(self, entity: T) -> None: ...

@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    value: T | None
    error: str | None = None
    
    @property
    def is_ok(self) -> bool:
        return self.error is None
```

**Configuration Validation**
```python
from pydantic import BaseModel, SecretStr, field_validator

class DatabaseConfig(BaseModel):
    host: str
    port: int
    password: SecretStr
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be 1-65535")
        return v
```

### Error Handling

**Structured Exception Hierarchy**
```python
class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}

class ValidationError(AppError):
    """Input validation failed."""

class ConnectionError(AppError):
    """External service unreachable."""

# Usage: raise specific, catch general
try:
    validate_input(data)
except ValidationError as e:
    logger.warning("Validation failed", extra=e.context)
    return Result(value=None, error=str(e))
```

**Context Managers for Resources**
```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def managed_connection(host: str) -> Iterator[Connection]:
    conn = Connection(host)
    try:
        conn.connect()
        yield conn
    finally:
        conn.disconnect()
```

### Logging Standards

**Structured Logging**
```python
import logging
from typing import Any

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger

# Log with context, not string interpolation
logger.info(
    "Operation completed",
    extra={"user_id": user.id, "duration_ms": elapsed, "status": "success"}
)
```

**Log Levels**
- `DEBUG`: Diagnostic details for developers
- `INFO`: Business events (user actions, state changes)
- `WARNING`: Recoverable issues (retries, fallbacks)
- `ERROR`: Failures requiring attention
- `CRITICAL`: System-wide failures

### Testing Patterns

**Arrange-Act-Assert**
```python
def test_user_creation():
    # Arrange
    user_data = {"name": "Test", "email": "test@example.com"}
    repo = InMemoryUserRepository()
    service = UserService(repo)
    
    # Act
    result = service.create_user(user_data)
    
    # Assert
    assert result.is_ok
    assert repo.get(result.value.id) is not None
```

**Dependency Injection for Testability**
```python
class OrderService:
    def __init__(
        self,
        repo: OrderRepository,
        notifier: Notifier,
        clock: Callable[[], datetime] = datetime.now,
    ):
        self._repo = repo
        self._notifier = notifier
        self._clock = clock  # Injectable for testing
```

## Anti-Patterns to Avoid

### Code Smells

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **God Class** | 1000+ line classes doing everything | Split by responsibility |
| **Primitive Obsession** | `user_id: str` everywhere | `UserId` newtype wrapper |
| **Stringly Typed** | `status: str` with magic values | `Status` enum |
| **Boolean Blindness** | `process(data, True, False, True)` | Named parameters or config object |
| **Shotgun Surgery** | One change requires 10 file edits | Consolidate related logic |
| **Feature Envy** | Method uses another class's data more than its own | Move method to that class |

### Configuration Anti-Patterns

**❌ Hardcoded Values**
```python
# Bad
timeout = 30
host = "192.168.1.1"
```

**✅ Externalized Configuration**
```python
# Good
@dataclass
class Config:
    timeout: int = field(default=30)
    host: str = field(default_factory=lambda: os.getenv("HOST", "localhost"))
```

### Error Handling Anti-Patterns

**❌ Pokemon Exception Handling**
```python
# Bad - catches everything, hides bugs
try:
    do_something()
except Exception:
    pass
```

**✅ Specific Exception Handling**
```python
# Good - explicit about what can fail
try:
    result = external_api.call()
except ConnectionError:
    logger.warning("API unavailable, using cache")
    result = cache.get()
except ValidationError as e:
    raise AppError(f"Invalid response: {e}") from e
```

### Testing Anti-Patterns

**❌ Testing Implementation Details**
```python
# Bad - breaks when refactoring
def test_user_service():
    service.create_user(data)
    assert service._internal_cache["user_1"] is not None
```

**✅ Testing Behavior**
```python
# Good - tests contract, not internals
def test_user_service():
    result = service.create_user(data)
    assert service.get_user(result.id) is not None
```

### Dependency Anti-Patterns

**❌ Hidden Dependencies**
```python
# Bad - imports global state
class UserService:
    def save(self, user):
        db.session.add(user)  # Where does db come from?
```

**✅ Explicit Dependencies**
```python
# Good - dependencies are visible
class UserService:
    def __init__(self, session: Session):
        self._session = session
```

## Implementation Guidelines

### 1. Project Setup

```bash
# Initialize with modern tooling
uv init project-name
cd project-name

# Configure ruff (pyproject.toml)
[tool.ruff]
line-length = 88
target-version = "py312"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "RUF"]

[tool.ruff.isort]
known-first-party = ["src"]

# Configure mypy
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
```

### 2. Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic]
```

### 3. CI Pipeline Stages

1. **Lint**: `ruff check .`
2. **Format Check**: `ruff format --check .`
3. **Type Check**: `mypy .`
4. **Test**: `pytest --cov=src --cov-fail-under=80`
5. **Security**: `bandit -r src/`

### 4. Code Review Checklist

- [ ] Types complete and correct
- [ ] Error cases handled explicitly
- [ ] Logging includes context
- [ ] No hardcoded secrets/config
- [ ] Tests cover happy path + edge cases
- [ ] Docstrings on public API
- [ ] No TODO without issue reference

### 5. Documentation Standards

```python
def process_order(
    order: Order,
    *,
    validate: bool = True,
    notify: bool = True,
) -> Result[ProcessedOrder]:
    """Process an order through the fulfillment pipeline.
    
    Args:
        order: The order to process.
        validate: Whether to validate inventory before processing.
        notify: Whether to send customer notification on completion.
    
    Returns:
        Result containing ProcessedOrder on success, error message on failure.
    
    Raises:
        ValidationError: If order data is malformed.
        
    Example:
        >>> result = process_order(order, validate=True)
        >>> if result.is_ok:
        ...     print(f"Processed: {result.value.id}")
    """
```

## Success Metrics

### Code Quality Metrics

| Metric | Target | Tool |
|--------|--------|------|
| Type Coverage | >95% | mypy --txt-report |
| Test Coverage | >80% | pytest-cov |
| Cyclomatic Complexity | <10 per function | radon |
| Lint Violations | 0 | ruff |
| Security Issues | 0 critical/high | bandit |

### Process Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| PR Review Time | <24h | Git analytics |
| CI Pipeline Duration | <10min | CI dashboard |
| Deployment Frequency | Daily capable | Release logs |
| Mean Time to Recovery | <1h | Incident tracking |

### Team Health Indicators

- **Onboarding Time**: New developer productive in <1 week
- **Code Ownership**: No single-person knowledge silos
- **Technical Debt Ratio**: <10% of sprint capacity on maintenance
- **Documentation Currency**: README updated within 1 week of changes

## Sources & References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) — Official Python style guide
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/) — Type annotation specification
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) — Comprehensive style guide with docstring conventions
- [Ruff Documentation](https://docs.astral.sh/ruff/) — Modern Python linter and formatter
- [mypy Documentation](https://mypy.readthedocs.io/) — Static type checker for Python
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/) — Data validation using Python type annotations
- [Martin Fowler - Code Smells](https://refactoring.guru/refactoring/smells) — Catalog of code smells and refactoring techniques
- [The Twelve-Factor App](https://12factor.net/) — Methodology for building modern applications
- [Python Testing with pytest](https://docs.pytest.org/) — Testing framework best practices

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
