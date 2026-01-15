---
title:        Error Handling Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Error Handling Patterns

## Core Principles

1. **Fail Fast, Fail Loud**: Detect errors at the earliest possible point and surface them immediately rather than allowing silent failures to propagate through the system.

2. **Be Specific**: Use precise exception types that communicate exactly what went wrong. Generic exceptions hide information and make debugging harder.

3. **Preserve Context**: Always capture and propagate the original error context (stack traces, variable state, timestamps) when re-raising or wrapping exceptions.

4. **Handle at the Right Level**: Catch exceptions only where you can meaningfully handle them. Don't catch exceptions just to log and re-raise at every layer.

5. **Make Errors Recoverable When Possible**: Design error handling to enable graceful degradation and recovery rather than catastrophic failure.

## Essential Patterns

### Result Type Pattern (Explicit Error Returns)

Prefer explicit error returns over exceptions for expected failure modes:

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

def parse_config(path: str) -> Result[Config, ConfigError]:
    """Returns Result instead of raising - caller must handle both cases."""
    try:
        data = Path(path).read_text()
        return Ok(Config.model_validate_json(data))
    except FileNotFoundError:
        return Err(ConfigError(f"Config not found: {path}"))
    except ValidationError as e:
        return Err(ConfigError(f"Invalid config: {e}"))
```

**When to use**: Business logic with expected failure modes, API boundaries, parsing/validation.

### Exception Hierarchy Pattern

Create domain-specific exception hierarchies:

```python
class AppError(Exception):
    """Base exception for application errors."""
    
    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code
        self.timestamp = datetime.now(UTC)

class NetworkError(AppError):
    """Network-related failures."""

class ConnectionError(NetworkError):
    """Failed to establish connection."""

class TimeoutError(NetworkError):
    """Operation timed out."""

class ValidationError(AppError):
    """Input validation failures."""
```

**Benefits**: Enables selective catching, clear error categorization, consistent error metadata.

### Context Manager for Resource Cleanup

Guarantee cleanup regardless of success/failure:

```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def managed_connection(host: str) -> Iterator[Connection]:
    """Ensures connection cleanup on any exit path."""
    conn = Connection(host)
    try:
        conn.connect()
        yield conn
    except ConnectionError:
        logger.exception("Connection failed to %s", host)
        raise
    finally:
        conn.disconnect()  # Always runs

# Usage
with managed_connection("10.0.0.1") as conn:
    conn.execute("command")  # Cleanup guaranteed even if this raises
```

### Exception Chaining (Preserve Root Cause)

Always chain exceptions to preserve the original cause:

```python
def load_user(user_id: int) -> User:
    try:
        data = database.fetch(user_id)
        return User.model_validate(data)
    except DatabaseError as e:
        # Chain with 'from e' - preserves original traceback
        raise UserLoadError(f"Failed to load user {user_id}") from e
```

### Retry with Exponential Backoff

Handle transient failures gracefully:

```python
import random
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

def retry(
    func: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Retry with exponential backoff and jitter."""
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            if attempt == max_attempts - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning("Attempt %d failed: %s. Retrying in %.1fs", attempt + 1, e, delay)
            time.sleep(delay)
    raise RuntimeError("Unreachable")  # Type checker satisfaction
```

### Structured Error Logging

Log errors with consistent, queryable structure:

```python
import structlog

logger = structlog.get_logger()

def process_request(request_id: str, payload: dict) -> None:
    log = logger.bind(request_id=request_id)
    try:
        result = do_processing(payload)
        log.info("request_processed", result_size=len(result))
    except ValidationError as e:
        log.warning("validation_failed", errors=e.errors(), payload_keys=list(payload.keys()))
        raise
    except Exception:
        log.exception("request_failed", payload_size=len(payload))
        raise
```

### Guard Clauses (Early Return)

Validate preconditions early and exit fast:

```python
def transfer_funds(from_account: str, to_account: str, amount: Decimal) -> TransferResult:
    # Guard clauses - fail fast with specific errors
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")
    
    if from_account == to_account:
        raise ValueError("Cannot transfer to same account")
    
    source = get_account(from_account)
    if source is None:
        raise AccountNotFoundError(from_account)
    
    if source.balance < amount:
        raise InsufficientFundsError(source.balance, amount)
    
    # Happy path - all preconditions satisfied
    return execute_transfer(source, to_account, amount)
```

## Anti-Patterns to Avoid

### 1. Pokemon Exception Handling ("Gotta Catch 'Em All")

```python
# ❌ BAD: Catches everything, hides bugs
try:
    result = complex_operation()
except Exception:
    pass  # Silent failure - bugs disappear here

# ✅ GOOD: Catch specific exceptions, handle appropriately
try:
    result = complex_operation()
except NetworkError as e:
    logger.warning("Network issue, using cached data: %s", e)
    result = get_cached_result()
except ValidationError as e:
    raise InvalidInputError(f"Bad input: {e}") from e
```

### 2. Exception as Control Flow

```python
# ❌ BAD: Using exceptions for expected conditions
def find_user(user_id: int) -> User:
    try:
        return users[user_id]
    except KeyError:
        return create_default_user()  # Expected case, not exceptional

# ✅ GOOD: Use conditional logic for expected cases
def find_user(user_id: int) -> User:
    if user_id in users:
        return users[user_id]
    return create_default_user()
```

### 3. Swallowing Exceptions

```python
# ❌ BAD: Logging then ignoring
try:
    save_to_database(data)
except DatabaseError as e:
    logger.error("Database error: %s", e)
    # Continues as if nothing happened - data loss!

# ✅ GOOD: Handle meaningfully or propagate
try:
    save_to_database(data)
except DatabaseError as e:
    logger.error("Database error, queuing for retry: %s", e)
    retry_queue.add(data)  # Actual handling
    raise  # Or propagate if can't handle
```

### 4. Bare Raise in Wrong Context

```python
# ❌ BAD: Bare raise outside except block
def process(data):
    if not data:
        raise  # RuntimeError: No active exception

# ✅ GOOD: Raise specific exception
def process(data):
    if not data:
        raise ValueError("Data cannot be empty")
```

### 5. Losing Exception Context

```python
# ❌ BAD: Loses original traceback
try:
    parse_config(path)
except ParseError as e:
    raise ConfigError(str(e))  # Original traceback lost!

# ✅ GOOD: Chain exceptions
try:
    parse_config(path)
except ParseError as e:
    raise ConfigError(f"Config parse failed: {path}") from e
```

### 6. Overly Broad Exception Types

```python
# ❌ BAD: Catches unrelated errors
try:
    user = users[user_id]
    result = user.process(data)
except Exception:  # Catches KeyError, AttributeError, bugs...
    return None

# ✅ GOOD: Catch only expected exceptions
try:
    user = users[user_id]
except KeyError:
    raise UserNotFoundError(user_id)
# Let other exceptions propagate - they're bugs
result = user.process(data)
```

### 7. Nested Try-Except Pyramids

```python
# ❌ BAD: Deeply nested error handling
try:
    conn = connect()
    try:
        data = conn.fetch()
        try:
            result = process(data)
        except ProcessError:
            ...
    except FetchError:
        ...
except ConnectError:
    ...

# ✅ GOOD: Use context managers and early returns
with managed_connection() as conn:
    data = conn.fetch()  # Let FetchError propagate
    return process(data)  # Let ProcessError propagate
```

## Implementation Guidelines

### Step 1: Define Error Taxonomy

1. Identify failure modes in your domain
2. Create base exception class with common metadata
3. Build hierarchy: `AppError` → `NetworkError` → `ConnectionError`
4. Document when each exception type should be raised

### Step 2: Choose Error Strategy Per Layer

| Layer | Strategy |
|-------|----------|
| Domain/Business Logic | Result types for expected failures |
| Infrastructure | Exceptions with retry logic |
| API Boundaries | Catch and transform to API errors |
| Entry Points | Global handler for unhandled exceptions |

### Step 3: Implement Consistent Logging

```python
# Configure structured logging once
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
)

# Use consistently
logger.exception("operation_failed", operation="save_user", user_id=user_id)
```

### Step 4: Add Error Recovery Mechanisms

1. Implement retry logic for transient failures
2. Add circuit breakers for external dependencies
3. Design fallback behaviors (cached data, degraded mode)
4. Queue failed operations for later retry

### Step 5: Test Error Paths

```python
def test_connection_failure_triggers_retry():
    mock_conn = Mock(side_effect=[ConnectionError, ConnectionError, Success()])
    result = retry(mock_conn.connect, max_attempts=3)
    assert mock_conn.call_count == 3

def test_validation_error_includes_field_info():
    with pytest.raises(ValidationError) as exc_info:
        validate_user({"email": "invalid"})
    assert "email" in str(exc_info.value)
```

## Success Metrics

### Observability Metrics

- **Error Rate**: Errors per request/operation (target: <1%)
- **Mean Time to Detection (MTTD)**: Time from error occurrence to alert
- **Mean Time to Resolution (MTTR)**: Time from detection to fix

### Code Quality Metrics

- **Exception Specificity**: Ratio of specific to generic exception catches
- **Error Context Completeness**: % of errors with full context (traceback, request ID, timestamp)
- **Recovery Rate**: % of transient errors successfully retried

### Operational Metrics

- **Silent Failure Rate**: Errors caught but not logged (target: 0%)
- **Unhandled Exception Rate**: Exceptions reaching global handler
- **Error Log Queryability**: Can errors be filtered by type, service, user?

### Review Checklist

- [ ] All exceptions have specific types (no bare `except:`)
- [ ] Exception chains preserve original cause (`from e`)
- [ ] Resources cleaned up via context managers
- [ ] Transient failures have retry logic
- [ ] Errors logged with structured context
- [ ] Error paths have test coverage

## Sources & References

- [PEP 3134 - Exception Chaining](https://peps.python.org/pep-3134/) — Exception chaining and `__cause__` attribute
- [Python Documentation - Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html) — Official exception handling guide
- [Python Documentation - contextlib](https://docs.python.org/3/library/contextlib.html) — Context manager utilities
- [structlog Documentation](https://www.structlog.org/) — Structured logging library
- [Effective Python, 3rd Edition](https://effectivepython.com/) — Item 65-70 on exception handling
- [Architecture Patterns with Python](https://www.cosmicpython.com/) — Domain error handling patterns

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
