---
title:        Error Handling Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Error Handling Best Practices

## Core Principles

1. **Fail Fast, Fail Explicitly**: Detect errors at the earliest possible point and surface them immediately with clear, actionable messages. Silent failures are debugging nightmares.

2. **Errors as Data, Not Control Flow**: Treat errors as first-class values using Result types or explicit return values where appropriate. Exceptions should be exceptional, not routine control flow.

3. **Preserve Context Through the Stack**: Always chain exceptions with `raise ... from` to maintain the full error context. Lost context means lost debugging time.

4. **Handle at the Right Level**: Catch exceptions only where you can meaningfully handle them. Don't catch-and-ignore; don't catch-and-rethrow without adding value.

5. **Type-Safe Error Contracts**: Use type hints to document what errors a function can produce. Make error handling explicit in function signatures.

## Essential Practices

### Exception Handling Patterns

```python
# ✅ Narrow try blocks - catch specific exceptions
def parse_config(path: Path) -> Config:
    try:
        content = path.read_text()
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}") from None
    except PermissionError as e:
        raise ConfigError(f"Cannot read config: {path}") from e
    
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e.msg}") from e
    
    return Config.model_validate(data)

# ✅ Exception chaining preserves context
try:
    result = external_api_call()
except RequestException as e:
    raise ServiceUnavailableError("API unreachable") from e

# ✅ Use else for success path, finally for cleanup
try:
    conn = acquire_connection()
except ConnectionError:
    logger.error("Failed to connect")
    raise
else:
    process_data(conn)
finally:
    conn.close()
```

### Result Type Pattern (Functional Approach)

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    value: T
    
    def is_ok(self) -> bool:
        return True
    
    def unwrap(self) -> T:
        return self.value

@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    error: E
    
    def is_ok(self) -> bool:
        return False
    
    def unwrap(self) -> Never:
        raise self.error

Result = Union[Ok[T], Err[E]]

# Usage
def divide(a: float, b: float) -> Result[float, ValueError]:
    if b == 0:
        return Err(ValueError("Division by zero"))
    return Ok(a / b)

match divide(10, 0):
    case Ok(value):
        print(f"Result: {value}")
    case Err(error):
        logger.error(f"Failed: {error}")
```

### Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base exception for application errors."""
    
    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.code = code

class ValidationError(AppError):
    """Input validation failed."""
    pass

class ConfigError(AppError):
    """Configuration error."""
    pass

class ServiceError(AppError):
    """External service error."""
    
    def __init__(
        self, 
        message: str, 
        *, 
        service: str,
        retryable: bool = False,
    ):
        super().__init__(message, code=f"SERVICE_{service.upper()}")
        self.service = service
        self.retryable = retryable
```

### Structured Logging for Errors

```python
import structlog

logger = structlog.get_logger()

def process_order(order_id: str) -> None:
    log = logger.bind(order_id=order_id)
    
    try:
        order = fetch_order(order_id)
        log.info("order_fetched", status=order.status)
        
        result = process(order)
        log.info("order_processed", result=result)
        
    except ValidationError as e:
        log.warning("validation_failed", error=str(e), code=e.code)
        raise
    except ServiceError as e:
        log.error(
            "service_error",
            error=str(e),
            service=e.service,
            retryable=e.retryable,
            exc_info=True,
        )
        raise
    except Exception:
        log.exception("unexpected_error")
        raise
```

### Exception Groups (Python 3.11+)

```python
async def fetch_all(urls: list[str]) -> list[Response]:
    """Fetch multiple URLs, collecting all errors."""
    results = []
    errors = []
    
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch(url)) for url in urls]
    
    # TaskGroup raises ExceptionGroup on failures
    return [t.result() for t in tasks]

# Handle with except*
try:
    results = await fetch_all(urls)
except* ConnectionError as eg:
    for exc in eg.exceptions:
        logger.error(f"Connection failed: {exc}")
except* TimeoutError as eg:
    logger.warning(f"{len(eg.exceptions)} requests timed out")
```

### Context Managers for Resource Safety

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def managed_transaction(conn: Connection) -> Generator[Transaction, None, None]:
    """Transaction with automatic rollback on error."""
    tx = conn.begin()
    try:
        yield tx
        tx.commit()
    except Exception:
        tx.rollback()
        raise
```

## Anti-Patterns to Avoid

### ❌ Bare Except Clauses
```python
# BAD: Catches SystemExit, KeyboardInterrupt
try:
    risky_operation()
except:
    pass

# GOOD: Catch specific exceptions
try:
    risky_operation()
except (ValueError, TypeError) as e:
    handle_error(e)
```

### ❌ Swallowing Exceptions
```python
# BAD: Silent failure
try:
    save_data(data)
except Exception:
    pass  # Data loss with no indication

# GOOD: Log and handle appropriately
try:
    save_data(data)
except IOError as e:
    logger.error("save_failed", error=str(e), exc_info=True)
    raise DataPersistenceError("Failed to save") from e
```

### ❌ Overly Broad Try Blocks
```python
# BAD: Can't tell which operation failed
try:
    config = load_config()
    data = fetch_data(config.url)
    result = process(data)
    save(result)
except Exception as e:
    print(f"Something failed: {e}")

# GOOD: Narrow scope, specific handling
config = load_config()  # Let config errors propagate
try:
    data = fetch_data(config.url)
except RequestError as e:
    raise DataFetchError(f"Failed to fetch from {config.url}") from e
```

### ❌ Using Exceptions for Control Flow
```python
# BAD: Exception as expected path
def find_user(user_id: str) -> User:
    try:
        return users[user_id]
    except KeyError:
        return create_default_user()

# GOOD: Explicit check
def find_user(user_id: str) -> User:
    if user_id in users:
        return users[user_id]
    return create_default_user()
```

### ❌ Losing Exception Context
```python
# BAD: Original traceback lost
try:
    operation()
except ValueError:
    raise RuntimeError("Operation failed")

# GOOD: Chain exceptions
try:
    operation()
except ValueError as e:
    raise RuntimeError("Operation failed") from e
```

### ❌ Catching and Re-raising Without Value
```python
# BAD: Pointless catch
try:
    operation()
except ValueError:
    raise

# GOOD: Add context or handle
try:
    operation()
except ValueError as e:
    logger.error("operation_failed", error=str(e))
    raise OperationError("Context about what failed") from e
```

## Implementation Guidelines

### Step 1: Define Error Taxonomy
1. Create base exception class for your application
2. Define domain-specific exception subclasses
3. Include error codes for machine-readable identification
4. Add structured attributes (retryable, severity, etc.)

### Step 2: Establish Logging Strategy
1. Use structured logging (structlog, python-json-logger)
2. Include correlation IDs for request tracing
3. Log at appropriate levels: ERROR for failures, WARNING for recoverable issues
4. Always include `exc_info=True` for unexpected exceptions

### Step 3: Implement Error Boundaries
1. Define clear boundaries where errors are caught and transformed
2. API layer: Convert internal exceptions to HTTP responses
3. Service layer: Wrap external service failures
4. Repository layer: Wrap database/storage errors

### Step 4: Add Retry Logic Where Appropriate
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(ServiceError),
)
def call_external_service() -> Response:
    return client.request()
```

### Step 5: Test Error Paths
1. Unit test each exception type
2. Test exception chaining preserves context
3. Test retry behavior and circuit breakers
4. Test error responses at API boundaries

## Success Metrics

### Code Quality Metrics
- **Exception specificity**: < 5% of except clauses catch `Exception` or broader
- **Context preservation**: 100% of re-raised exceptions use `from` clause
- **Try block scope**: Average < 5 statements per try block

### Operational Metrics
- **Error categorization**: > 95% of errors have specific exception types
- **Debugging time**: Mean time to identify root cause < 15 minutes
- **Alert actionability**: > 90% of error alerts lead to specific remediation

### Observability Metrics
- **Structured logging coverage**: 100% of error logs include correlation ID
- **Stack trace availability**: 100% of unexpected errors include full traceback
- **Error rate tracking**: Per-endpoint and per-service error rates monitored

### Recovery Metrics
- **Retry success rate**: > 80% of retryable errors succeed on retry
- **Graceful degradation**: Critical paths have fallback behavior defined
- **MTTR (Mean Time to Recovery)**: < 30 minutes for P1 incidents

## Sources & References

- [Professional Guide to Python Exception Handling](https://derekarmstrong.dev/blog/professional-guide-to-python-exception-handling/) — Comprehensive guide covering basic to advanced patterns (2025)
- [Python Error Handling Complete Guide](https://generalistprogrammer.com/tutorials/python-error-handling-complete-guide) — Full tutorial on exception handling mechanisms (2025)
- [6 Best Practices for Python Exception Handling](https://www.codium.ai/blog/6-best-practices-for-python-exception-handling/) — Enterprise-focused exception handling practices (2025)
- [Python Error Handling: 10 Enterprise-Grade Tactics](https://www.augmentcode.com/guides/python-error-handling-10-enterprise-grade-tactics) — Production system patterns achieving 79% less downtime (2025)
- [dry-python/returns](https://github.com/dry-python/returns) — Type-safe Result types and functional error handling for Python
- [Python Logging with Structlog](https://last9.io/blog/python-logging-with-structlog/) — Structured logging for better observability (2024)
- [PEP 654 – Exception Groups and except*](https://peps.python.org/pep-0654/) — Python 3.11+ exception groups specification
- [Advanced Python Logging for Production Systems](https://geekcafe.com/blog/2024/05/advanced-python-logging) — Production logging strategies (2024)
- [Mastering Custom Exception Handling Patterns](https://binaryscripts.com/python/2024/12/11/implementing-custom-exception-handling-patterns-in-python.html) — Custom exception design patterns (2024)
- [Python Try Except: Examples and Best Practices](https://python.land/deep-dives/python-try-except) — Exception hierarchy and best practices (2024)

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
