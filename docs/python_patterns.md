---
title:        Python Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Python Patterns

## Core Principles

1. **Explicit is better than implicit** - Favor clear, readable code over clever one-liners. Type hints, explicit returns, and named parameters improve maintainability.

2. **Composition over inheritance** - Prefer composing objects with clear interfaces rather than deep inheritance hierarchies. Use protocols and ABCs for contracts.

3. **Fail fast with rich errors** - Validate inputs early, use specific exception types, and provide actionable error messages. Never silently swallow exceptions.

4. **Immutability by default** - Use `frozen=True` dataclasses, avoid mutable default arguments, prefer returning new objects over mutation.

5. **Let the type system help** - Leverage `typing`, dataclasses, and Pydantic for compile-time safety. Run mypy/pyright in strict mode.

## Essential Patterns

### Data Modeling

**Use dataclasses for structured data:**
```python
from dataclasses import dataclass, field
from typing import Self

@dataclass(frozen=True, slots=True)
class Config:
    host: str
    port: int = 8080
    tags: tuple[str, ...] = field(default_factory=tuple)
    
    def with_port(self, port: int) -> Self:
        return Config(self.host, port, self.tags)
```

**Use Pydantic for validation and serialization:**
```python
from pydantic import BaseModel, Field, SecretStr

class Credentials(BaseModel):
    username: str = Field(min_length=1)
    password: SecretStr
    
    model_config = {"frozen": True}
```

### Iteration Patterns

**Use enumerate, zip, and comprehensions:**
```python
# Good: enumerate for index + value
for idx, item in enumerate(items):
    process(idx, item)

# Good: zip for parallel iteration
for name, score in zip(names, scores, strict=True):
    print(f"{name}: {score}")

# Good: comprehension with condition
valid = [x for x in data if x.is_valid()]

# Good: generator for large datasets
def process_large(items):
    yield from (transform(x) for x in items if x)
```

### Resource Management

**Always use context managers:**
```python
from contextlib import contextmanager
from pathlib import Path

# Good: automatic cleanup
with Path("data.txt").open() as f:
    content = f.read()

# Good: custom context manager
@contextmanager
def managed_connection(host: str):
    conn = Connection(host)
    try:
        conn.connect()
        yield conn
    finally:
        conn.disconnect()
```

### Error Handling

**Use specific exceptions with context:**
```python
from typing import Never

class ValidationError(Exception):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")

def validate_port(port: int) -> int:
    if not 1 <= port <= 65535:
        raise ValidationError("port", f"must be 1-65535, got {port}")
    return port

# Good: specific except clauses, ordered narrow to broad
try:
    result = risky_operation()
except ValidationError as e:
    logger.warning("Validation failed: %s", e)
    return default
except OSError as e:
    logger.error("IO error: %s", e)
    raise
```

### Result Pattern (Alternative to Exceptions)

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")

@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E

type Result[T, E] = Ok[T] | Err[E]

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"invalid integer: {s!r}")
```

### Dependency Injection

```python
from typing import Protocol

class Repository(Protocol):
    def get(self, id: str) -> dict | None: ...
    def save(self, id: str, data: dict) -> None: ...

class Service:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo
    
    def process(self, id: str) -> bool:
        if data := self._repo.get(id):
            # process data
            return True
        return False
```

### Factory Pattern

```python
from typing import Callable

type ParserFactory = Callable[[str], Parser]

def create_parser(format: str) -> Parser:
    parsers: dict[str, type[Parser]] = {
        "json": JsonParser,
        "yaml": YamlParser,
        "toml": TomlParser,
    }
    if parser_cls := parsers.get(format):
        return parser_cls()
    raise ValueError(f"unknown format: {format}")
```

### Singleton (When Actually Needed)

```python
from functools import cache

@cache
def get_config() -> Config:
    """Lazy singleton via caching."""
    return Config.from_file("config.toml")
```

## Anti-Patterns to Avoid

### Mutable Default Arguments

```python
# BAD: mutable default shared across calls
def append_to(item, target=[]):  # noqa: B006
    target.append(item)
    return target

# GOOD: use None sentinel
def append_to(item, target: list | None = None) -> list:
    if target is None:
        target = []
    target.append(item)
    return target
```

### Bare Except Clauses

```python
# BAD: catches SystemExit, KeyboardInterrupt
try:
    do_something()
except:
    pass

# BAD: too broad, hides bugs
try:
    do_something()
except Exception:
    pass

# GOOD: specific exceptions
try:
    do_something()
except (ValueError, KeyError) as e:
    logger.exception("Operation failed")
    raise
```

### Using range(len()) for Iteration

```python
# BAD: unpythonic, error-prone
for i in range(len(items)):
    print(items[i])

# GOOD: direct iteration
for item in items:
    print(item)

# GOOD: when index needed
for i, item in enumerate(items):
    print(i, item)
```

### Wildcard Imports

```python
# BAD: pollutes namespace, hides dependencies
from os.path import *
from typing import *

# GOOD: explicit imports
from os.path import join, exists
from typing import Any, TypeVar
```

### Not Using Context Managers

```python
# BAD: resource leak on exception
f = open("file.txt")
data = f.read()
f.close()

# GOOD: automatic cleanup
with open("file.txt") as f:
    data = f.read()
```

### Checking Membership in Lists

```python
# BAD: O(n) lookup
if item in large_list:
    process(item)

# GOOD: O(1) lookup
large_set = set(large_list)
if item in large_set:
    process(item)
```

### God Objects / Classes

```python
# BAD: class does everything
class Manager:
    def connect(self): ...
    def parse_data(self): ...
    def validate(self): ...
    def send_email(self): ...
    def generate_report(self): ...

# GOOD: single responsibility
class Connection: ...
class Parser: ...
class Validator: ...
class EmailSender: ...
class ReportGenerator: ...
```

### Stringly-Typed Code

```python
# BAD: magic strings
def process(status: str):
    if status == "pending":
        ...

# GOOD: enums for fixed values
from enum import StrEnum, auto

class Status(StrEnum):
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()

def process(status: Status):
    if status == Status.PENDING:
        ...
```

### Deep Nesting

```python
# BAD: arrow code
def process(data):
    if data:
        if data.is_valid():
            if data.has_permission():
                return do_work(data)
    return None

# GOOD: early returns (guard clauses)
def process(data):
    if not data:
        return None
    if not data.is_valid():
        return None
    if not data.has_permission():
        return None
    return do_work(data)
```

### Using eval/exec

```python
# BAD: security risk, hard to debug
result = eval(user_input)

# GOOD: use ast.literal_eval for safe literals
import ast
result = ast.literal_eval(user_input)

# BETTER: avoid dynamic code execution entirely
```

## Implementation Guidelines

### Project Setup

1. **Use modern tooling:**
   ```toml
   # pyproject.toml
   [tool.ruff]
   line-length = 88
   target-version = "py312"
   select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]
   
   [tool.mypy]
   strict = true
   python_version = "3.12"
   ```

2. **Structure code by feature, not layer:**
   ```
   src/
   ├── auth/
   │   ├── models.py
   │   ├── service.py
   │   └── repository.py
   ├── orders/
   │   ├── models.py
   │   ├── service.py
   │   └── repository.py
   └── shared/
       └── types.py
   ```

3. **Type everything:**
   - All function signatures
   - Class attributes
   - Module-level variables
   - Use `TypeVar`, `ParamSpec` for generics

### Code Review Checklist

- [ ] No mutable default arguments
- [ ] All exceptions are specific and handled appropriately
- [ ] Resources use context managers
- [ ] No wildcard imports
- [ ] Type hints on all public APIs
- [ ] No bare `except:` clauses
- [ ] Comprehensions used where appropriate
- [ ] No unnecessary `range(len())`
- [ ] Sets used for membership testing
- [ ] No global mutable state

### Refactoring Priorities

1. **Safety first:** Fix bare excepts, add type hints
2. **Readability:** Replace loops with comprehensions, add guard clauses
3. **Performance:** Profile before optimizing, use sets for lookups
4. **Maintainability:** Extract classes, reduce coupling

## Success Metrics

### Code Quality Indicators

| Metric | Target | Tool |
|--------|--------|------|
| Type coverage | >95% | mypy --strict |
| Lint errors | 0 | ruff check |
| Cyclomatic complexity | <10 per function | radon |
| Test coverage | >80% | pytest-cov |
| Security issues | 0 critical | bandit |

### Review Metrics

- **Anti-pattern density:** <1 per 500 LOC
- **Type hint coverage:** 100% of public APIs
- **Exception specificity:** No bare except clauses
- **Resource management:** 100% context manager usage for I/O

### Runtime Indicators

- No `TypeError` or `AttributeError` in production logs
- Exception traces show specific, actionable errors
- Memory usage stable (no leaks from unclosed resources)

## Sources & References

- [Anti-Patterns in Python Programming](https://lignos.org/py_antipatterns/) — Comprehensive guide to iteration, scope, and style anti-patterns
- [The Little Book of Python Anti-Patterns](http://docs.quantifiedcode.com/python-anti-patterns) — Categorized anti-patterns: correctness, maintainability, readability, security, performance
- [Python Design Patterns Best Practices](https://binaryscripts.com/python/2024/12/06/design-patterns-in-python-best-practices-for-large-scale-applications.html) — Design patterns for large-scale applications
- [Patterns and Antipatterns for Dataclasses](https://devinjcornell.com/post/dsp0_patterns_for_dataclasses.html) — Modern dataclass usage patterns
- [Statically Typed Functional Programming with Python 3.12](https://dotat.at/:/PW1CS) — ADTs and pattern matching with dataclasses
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/) — Official Python style guide
- [Python typing documentation](https://docs.python.org/3/library/typing.html) — Type hints reference

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
