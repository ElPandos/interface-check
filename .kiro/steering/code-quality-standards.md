---
title: Code Quality Standards
inclusion: always
---

# Code Quality Standards

## Type Hints and Annotations
- **Comprehensive Type Hints**: All functions, methods, and class attributes must include type hints
- **Union Types**: Use `Union[Type1, Type2]` or `Type1 | Type2` for multiple possible types
- **Optional Types**: Use `Optional[Type]` or `Type | None` for nullable values
- **Generic Collections**: Specify container types like `List[str]`, `Dict[str, Any]`, `queue.Queue[Sample]`
- **TypedDict**: Use for structured dictionaries with known keys (e.g., `HostDict`, `RouteDict`)

## Documentation Standards
- **Docstrings**: All classes and public methods require Google-style docstrings
- **Inline Comments**: Complex logic sections include explanatory comments
- **Type Documentation**: Complex type definitions documented with purpose and usage
- **Error Context**: Exception handling includes descriptive error messages

## Error Handling Patterns
- **Try-Catch Blocks**: Comprehensive exception handling with specific error types
- **Logging Integration**: All exceptions logged with `logging.exception()` for stack traces
- **Graceful Degradation**: UI operations continue with user notifications on errors
- **Bounds Checking**: Array/list access protected with range validation
- **Resource Cleanup**: Proper cleanup in finally blocks or context managers

## Code Quality Tools
- **Ruff**: Comprehensive linting and formatting (replaces Black + flake8)
- **Black**: Code formatting with 120 character line length (deprecated - use ruff format)
- **MyPy**: Strict type checking with no untyped definitions
- **Pre-commit**: Automated quality checks on commit
- **Pytest**: Testing framework with coverage reporting

## Development Workflow
- **Virtual Environments**: Use `uv` for dependency management
- **Reproducible Builds**: Lock file dependencies for consistency
- **Container Support**: Docker configuration for deployment
- **CI/CD**: GitHub Actions for automated testing and linting
