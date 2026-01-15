---
title:        Python Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Python Best Practices

## Core Principles

1. **Type Safety First**: Use comprehensive type annotations with `mypy --strict` or `pyright`. Types catch bugs at development time, improve IDE support, and serve as documentation.

2. **Modern Tooling**: Adopt `pyproject.toml` (PEP 621), `uv` or Poetry for dependency management, and Ruff for linting/formatting. These tools provide reproducible builds and deterministic environments.

3. **Explicit Over Implicit**: Prefer explicit error handling, clear function signatures, and well-defined data structures (dataclasses, Pydantic v2) over dynamic dictionaries and implicit behavior.

4. **Test-Driven Confidence**: Write tests with pytest, maintain high coverage on critical paths, and integrate testing into CI/CD pipelines.

5. **Security by Default**: Pin dependencies with lock files, scan for vulnerabilities, validate all inputs, and never hardcode secrets.

## Essential Practices

### Project Structure

Use the `src/` layout to prevent accidental imports during development:

```
project/
├── pyproject.toml
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── core.py
│       └── models.py
├── tests/
│   ├── test_core.py
│   └── conftest.py
└── README.md
```

### Type Annotations

```python
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")

@dataclass(frozen=True, slots=True)
class Result(Generic[T]):
    """Explicit success/failure container."""
    value: T | None
    error: str | None = None
    
    @property
    def success(self) -> bool:
        return self.error is None
```

**Guidelines:**
- Annotate all function signatures
- Use `TypedDict` for dictionary schemas from external sources
- Use `dataclasses` for internal data structures
- Use `Pydantic v2` when runtime validation is required
- Prefer `T | None` over `Optional[T]` (Python 3.10+)

### Dependency Management

```toml
# pyproject.toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "structlog>=24.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "mypy>=1.10",
    "ruff>=0.4",
]
```

**Commands:**
```bash
# Initialize project
uv init my-project
uv add pydantic structlog
uv add --dev pytest mypy ruff

# Run tools
uv run pytest
uv run mypy src/
uv run ruff check --fix .
```

### Code Quality Configuration

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "RUF"]

[tool.mypy]
strict = true
python_version = "3.12"
warn_return_any = true
warn_unused_ignores = true
```

### Error Handling

```python
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class AppError(Exception):
    """Structured application error."""
    code: str
    message: str
    details: dict[str, str] | None = None

def process_data(data: str) -> Result[dict]:
    """Process with explicit error handling."""
    try:
        parsed = parse_input(data)
        return Result(value=parsed)
    except ValueError as e:
        logger.warning("Invalid input: %s", e)
        return Result(value=None, error=f"Parse error: {e}")
    except Exception:
        logger.exception("Unexpected error processing data")
        raise
```

### Async Best Practices

```python
import asyncio
from collections.abc import AsyncIterator

async def fetch_all(urls: list[str]) -> list[str]:
    """Concurrent I/O with structured concurrency."""
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_url(url)) for url in urls]
    return [t.result() for t in tasks]

async def stream_data() -> AsyncIterator[bytes]:
    """Use async generators for streaming."""
    async for chunk in source.read_chunks():
        yield process(chunk)
```

**When to use async:**
- I/O-bound operations (network, file, database)
- High concurrency requirements
- Web APIs and servers

**When NOT to use async:**
- CPU-bound computation (use multiprocessing)
- Simple scripts
- When all dependencies are synchronous

### Structured Logging

```python
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()
logger.info("user_action", user_id=123, action="login")
```

### Testing with pytest

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def sample_data() -> dict[str, int]:
    return {"a": 1, "b": 2}

def test_process_data(sample_data: dict[str, int]) -> None:
    result = process(sample_data)
    assert result.success
    assert result.value == expected

@pytest.mark.parametrize("input,expected", [
    ("valid", True),
    ("", False),
    (None, False),
])
def test_validation(input: str | None, expected: bool) -> None:
    assert validate(input) == expected

@pytest.mark.asyncio
async def test_async_fetch() -> None:
    with patch("module.fetch", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": "test"}
        result = await fetch_data()
        assert result["data"] == "test"
```

## Anti-Patterns to Avoid

### Mutable Default Arguments
```python
# BAD
def append_to(item, target=[]):
    target.append(item)
    return target

# GOOD
def append_to(item, target: list | None = None) -> list:
    if target is None:
        target = []
    target.append(item)
    return target
```

### Bare Except Clauses
```python
# BAD
try:
    risky()
except:
    pass

# GOOD
try:
    risky()
except SpecificError as e:
    logger.warning("Expected error: %s", e)
except Exception:
    logger.exception("Unexpected error")
    raise
```

### Using `eval()` or `exec()`
Never execute arbitrary code from user input. Use safe alternatives like `ast.literal_eval()` for simple cases.

### Wildcard Imports
```python
# BAD
from module import *

# GOOD
from module import specific_function, SpecificClass
```

### God Objects and Deep Inheritance
- Prefer composition over inheritance
- Keep classes focused on single responsibility
- Use protocols/ABCs for interfaces

### Ignoring Type Checker Errors
```python
# BAD
result: str = get_data()  # type: ignore

# GOOD - Fix the actual issue
result = get_data()
if result is None:
    raise ValueError("Expected data")
```

### Magic Numbers and Strings
```python
# BAD
if status == 200:
    timeout = 30

# GOOD
HTTP_OK = 200
DEFAULT_TIMEOUT_SEC = 30

if status == HTTP_OK:
    timeout = DEFAULT_TIMEOUT_SEC
```

## Implementation Guidelines

### Starting a New Project

1. **Initialize with modern tooling:**
   ```bash
   uv init my-project --python 3.12
   cd my-project
   mkdir -p src/my_project tests
   ```

2. **Configure quality tools in `pyproject.toml`:**
   - Add ruff, mypy, pytest configurations
   - Set `requires-python = ">=3.12"`

3. **Set up pre-commit hooks:**
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.4.0
       hooks:
         - id: ruff
         - id: ruff-format
   ```

4. **Create CI pipeline:**
   ```yaml
   # .github/workflows/ci.yml
   - run: uv sync
   - run: uv run ruff check .
   - run: uv run mypy src/
   - run: uv run pytest --cov
   ```

### Migrating Existing Code

1. Add type annotations incrementally (start with public APIs)
2. Configure mypy with `--strict` on new code only
3. Replace `requirements.txt` with `pyproject.toml`
4. Adopt `src/` layout during next major refactor
5. Add tests for critical paths before refactoring

### Data Structure Selection

| Use Case | Recommended |
|----------|-------------|
| Internal data models | `@dataclass(frozen=True, slots=True)` |
| External API responses | `TypedDict` or Pydantic |
| Validated user input | Pydantic v2 `BaseModel` |
| Simple immutable records | `NamedTuple` |
| Configuration | Pydantic `BaseSettings` |

## Success Metrics

### Code Quality
- **Type coverage**: >95% of functions annotated
- **Mypy strict**: Zero errors in CI
- **Ruff**: Zero warnings in CI
- **Cyclomatic complexity**: <10 per function

### Testing
- **Line coverage**: >80% overall, >95% on critical paths
- **Test execution time**: <60s for unit tests
- **Flaky tests**: Zero tolerance

### Security
- **Dependency vulnerabilities**: Zero high/critical
- **Secrets in code**: Zero (use pre-commit hooks)
- **Input validation**: 100% of external inputs

### Performance
- **Startup time**: Measured and tracked
- **Memory usage**: Profiled for long-running services
- **Response latency**: P95 tracked for APIs

### Maintainability
- **Documentation**: All public APIs documented
- **Code review**: All changes reviewed
- **Technical debt**: Tracked and prioritized

## Sources & References

Content was rephrased for compliance with licensing restrictions.

- [Python Best Practices 2025 Guide](https://nerdleveltech.com/python-best-practices-the-2025-guide-for-clean-fast-and-secure-code) — Comprehensive guide covering tooling, testing, security
- [Modern Python Practices](https://www.stuartellis.name/articles/python-modern-practices/) — uv, pipx, and modern development workflows
- [Python Typing 2025](https://khaled-jallouli.medium.com/python-typing-in-2025-a-comprehensive-guide-d61b4f562b99) — Type annotation evolution and best practices
- [Dataclasses vs Pydantic vs TypedDict](https://www.hevalhazalkurt.com/blog/dataclasses-vs-pydantic-vs-typeddict-vs-namedtuple-in-python/) — Data structure comparison
- [Python Anti-Patterns](https://github.com/quantifiedcode/python-anti-patterns) — Common mistakes and how to avoid them
- [Python Structured Concurrency](https://applifting.io/blog/python-structured-concurrency) — Modern async patterns
- [Result Objects in Python](https://devthink.alteredcraft.com/articles/2024-11-12_taming-error-flow-with-result-objects-in-python/) — Functional error handling
- [Python Logging Libraries](https://betterstack.com/community/guides/logging/best-python-logging-libraries/) — structlog, loguru comparison
- [pytest Best Practices](https://obedmacallums.com/posts/testing-python-pytest) — Testing patterns and fixtures
- [PEP 621](https://peps.python.org/pep-0621/) — pyproject.toml metadata specification
- [PEP 695](https://peps.python.org/pep-0695/) — Type parameter syntax (Python 3.12+)
- [Ruff Documentation](https://docs.astral.sh/ruff/) — Fast Python linter
- [uv Documentation](https://docs.astral.sh/uv/) — Fast Python package manager

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
