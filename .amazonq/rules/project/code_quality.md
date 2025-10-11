# Code Quality Standards

## Type Hints Requirements
- **All functions and methods** must have complete type annotations
- **Return types** explicitly specified, including `None`
- **Union types** using `|` syntax: `str | None` (Python 3.10+)
- **Generic collections**: `List[str]`, `Dict[str, Any]`, `Queue[Sample]`
- **Complex types** documented with purpose and usage

## Documentation Standards
- **Google-style docstrings** for all public classes and methods
- **Args/Returns sections** with type information
- **Raises sections** for documented exceptions
- **Examples** for complex APIs

## Error Handling Patterns
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.exception("Context about what failed")
    # Graceful degradation or user notification
    return default_value
```

## Validation Commands
- **Linting**: `uv run ruff check . --fix`
- **Type checking**: `uv run mypy .`
- **Formatting**: `uv run black .`
- **Testing**: `uv run pytest --cov=src`

## Code Style
- **Line length**: 120 characters
- **Imports**: Sorted with `isort`, grouped logically
- **Naming**: Snake_case for functions/variables, PascalCase for classes
- **Constants**: UPPER_CASE with type annotations