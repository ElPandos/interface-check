---
title:        Code Quality Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Code Quality Best Practices

## Core Principles

### 1. Type Safety First
Static typing catches bugs before runtime. Use type hints comprehensively and enforce with static analyzers (mypy --strict, pyright). Type annotations improve readability, enable IDE features, and serve as executable documentation.

### 2. Single Responsibility & Simplicity
Each module, class, and function should have one clear purpose. Apply SOLID principles, especially Single Responsibility (SRP) and Interface Segregation (ISP). Keep cyclomatic complexity under 10 per function.

### 3. Automated Quality Gates
Integrate linting, formatting, type checking, and testing into CI/CD pipelines. Quality checks must pass before merge. Automate everything that can be automated—humans review intent and architecture, machines check syntax and style.

### 4. Continuous Refactoring
Technical debt compounds. Address code smells immediately. Refactor as you go rather than accumulating debt for "later." The best time to fix bad code is when you're already touching it.

### 5. Explicit Over Implicit
Favor explicit error handling, clear naming, and documented assumptions. Avoid magic numbers, hidden state, and implicit type conversions. Code should communicate intent without requiring archaeology.

## Essential Practices

### Type Annotations
```python
# Always annotate function signatures
def process_data(
    items: list[dict[str, Any]],
    timeout: float = 30.0,
) -> Result[ProcessedData, ProcessingError]:
    """Process items with timeout."""
    ...

# Use TypedDict for structured dicts
class UserConfig(TypedDict):
    name: str
    email: str
    preferences: NotRequired[dict[str, str]]

# Prefer dataclasses/Pydantic for data containers
@dataclass(frozen=True, slots=True)
class Measurement:
    timestamp: datetime
    value: float
    unit: str
```

### Linting & Formatting
Use Ruff as unified linter/formatter (replaces Black, Flake8, isort):

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "SIM", "ARG", "PTH", "RUF"]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Static Type Checking
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
```

### Testing Strategy
- **Unit tests**: Fast, isolated, high coverage (>80% for critical paths)
- **Integration tests**: Verify component interactions
- **Property-based tests**: Use Hypothesis for edge case discovery
- **Mutation testing**: Validate test effectiveness

```python
# Test structure: Arrange-Act-Assert
def test_parser_extracts_metrics() -> None:
    # Arrange
    raw_output = "Temperature: 45.5C\nVoltage: 3.3V"
    parser = MetricParser()
    
    # Act
    result = parser.parse(raw_output)
    
    # Assert
    assert result.temperature == 45.5
    assert result.voltage == 3.3
```

### Error Handling
```python
# Use explicit Result types or rich exceptions
from typing import TypeVar, Generic

T = TypeVar("T")
E = TypeVar("E", bound=Exception)

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

Result = Ok[T] | Err[E]

# Or use structured exceptions with context
class ConnectionError(Exception):
    def __init__(self, host: str, port: int, cause: str) -> None:
        self.host = host
        self.port = port
        self.cause = cause
        super().__init__(f"Failed to connect to {host}:{port}: {cause}")
```

### Documentation Standards
```python
def calculate_throughput(
    bytes_transferred: int,
    duration_seconds: float,
    *,
    include_overhead: bool = False,
) -> float:
    """Calculate network throughput in Mbps.
    
    Args:
        bytes_transferred: Total bytes transferred.
        duration_seconds: Transfer duration in seconds.
        include_overhead: Include protocol overhead in calculation.
    
    Returns:
        Throughput in megabits per second.
    
    Raises:
        ValueError: If duration_seconds is zero or negative.
    
    Example:
        >>> calculate_throughput(1_000_000, 1.0)
        8.0
    """
    if duration_seconds <= 0:
        raise ValueError(f"Duration must be positive, got {duration_seconds}")
    
    bits = bytes_transferred * 8
    if include_overhead:
        bits *= 1.03  # ~3% protocol overhead
    
    return bits / duration_seconds / 1_000_000
```

### Code Review Checklist
1. **Correctness**: Does it solve the stated problem?
2. **Types**: Are all signatures annotated? Does mypy pass?
3. **Tests**: Are edge cases covered? Do tests verify behavior, not implementation?
4. **Naming**: Are names descriptive and consistent?
5. **Complexity**: Can any function be simplified or split?
6. **Security**: Input validation? No hardcoded secrets?
7. **Performance**: Any obvious inefficiencies? N+1 queries?

## Anti-Patterns to Avoid

### God Objects / Blob Classes
Classes that do everything. Split into focused, single-responsibility components.

```python
# BAD: God class
class ApplicationManager:
    def connect_database(self): ...
    def send_email(self): ...
    def process_payment(self): ...
    def generate_report(self): ...
    def validate_user(self): ...

# GOOD: Focused classes
class DatabaseConnection: ...
class EmailService: ...
class PaymentProcessor: ...
```

### Spaghetti Code
Tangled control flow with deep nesting. Use early returns, extract functions.

```python
# BAD: Deep nesting
def process(data):
    if data:
        if data.is_valid:
            if data.type == "A":
                # 4 levels deep...

# GOOD: Early returns
def process(data: Data | None) -> Result:
    if not data:
        return Err(MissingDataError())
    if not data.is_valid:
        return Err(ValidationError())
    
    return _process_by_type(data)
```

### Magic Numbers / Strings
Unexplained literals scattered through code.

```python
# BAD
if response.status == 429:
    time.sleep(60)

# GOOD
RATE_LIMIT_STATUS = 429
RATE_LIMIT_BACKOFF_SECONDS = 60

if response.status == RATE_LIMIT_STATUS:
    time.sleep(RATE_LIMIT_BACKOFF_SECONDS)
```

### Premature Optimization
Optimizing before measuring. Profile first, optimize bottlenecks.

### Copy-Paste Programming
Duplicated code. Extract shared logic into functions/classes.

### Ignoring Errors
Bare `except:` or swallowing exceptions silently.

```python
# BAD
try:
    risky_operation()
except:
    pass

# GOOD
try:
    risky_operation()
except SpecificError as e:
    logger.exception("Operation failed", error=str(e))
    raise OperationFailedError(cause=e) from e
```

### Stringly Typed Code
Using strings where enums or types belong.

```python
# BAD
def set_status(status: str): ...
set_status("actve")  # Typo undetected

# GOOD
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

def set_status(status: Status): ...
```

## Implementation Guidelines

### Step 1: Establish Tooling
1. Configure `pyproject.toml` with Ruff, mypy, pytest
2. Set up pre-commit hooks for automated checks
3. Configure CI pipeline to run all quality gates

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Step 2: Incremental Type Coverage
1. Start with `mypy --strict` on new code
2. Add type stubs for untyped dependencies
3. Gradually annotate existing code, module by module
4. Track coverage with `mypy --txt-report`

### Step 3: Test Infrastructure
1. Establish test directory structure mirroring source
2. Configure pytest with coverage reporting
3. Set minimum coverage thresholds (start at 60%, increase to 80%)
4. Add mutation testing for critical paths

### Step 4: Code Review Process
1. Require PR reviews before merge
2. Use automated checks as first gate
3. Focus human review on design, intent, edge cases
4. Document decisions in PR descriptions

### Step 5: Continuous Improvement
1. Track metrics over time (complexity, coverage, debt)
2. Schedule regular refactoring sessions
3. Conduct post-mortems on production issues
4. Update standards based on lessons learned

## Success Metrics

### Quantitative Metrics
| Metric | Target | Critical |
|--------|--------|----------|
| Type coverage | >90% | >70% |
| Test coverage (line) | >80% | >60% |
| Cyclomatic complexity (max) | <10 | <15 |
| Code duplication | <3% | <5% |
| Linting errors | 0 | 0 |
| Type errors | 0 | 0 |

### Qualitative Indicators
- **Time to onboard**: New developers productive within 1 week
- **Bug escape rate**: <5% of bugs reach production
- **Refactoring confidence**: Changes don't break unrelated features
- **Review turnaround**: PRs reviewed within 24 hours
- **Technical debt trend**: Decreasing or stable over time

### Measurement Tools
- **SonarQube/CodeClimate**: Comprehensive quality dashboards
- **pytest-cov**: Test coverage reporting
- **radon**: Cyclomatic complexity analysis
- **mypy --txt-report**: Type coverage tracking
- **Ruff**: Linting and style enforcement

## Sources & References

- [AWS Code Quality Explained](https://aws.amazon.com/what-is/code-quality/) — Comprehensive overview of code quality dimensions
- [Cortex Code Quality Metrics](https://www.cortex.io/post/measuring-and-improving-code-quality) — Metrics definitions and measurement approaches
- [Clean Code in Python](https://testdriven.io/blog/clean-code-python/) — Python-specific clean code practices
- [Type Checking in Python](https://www.turingtaco.com/type-checking-in-python-catching-bugs-before-they-bite/) — mypy, pyright, pyre comparison
- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/) — Official Ruff documentation
- [Software Quality Metrics 2025](https://blog.umano.tech/7-software-quality-metrics-to-track-in-2025) — Current metric recommendations
- [Anti-Patterns Guide](https://www.baeldung.com/cs/anti-patterns) — Common anti-patterns and solutions
- [Code Review Best Practices](https://www.cortex.io/post/best-practices-for-code-reviews) — Effective review processes
- [SOLID, DRY, KISS Principles](https://www.pullchecklist.com/posts/clean-code-principles) — Foundational design principles
- [Technical Debt Tracking](https://www.codeant.ai/blogs/track-technical-debt) — Measuring and managing debt

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version
