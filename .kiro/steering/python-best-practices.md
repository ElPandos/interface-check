---
title:        Python Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# Python Best Practices

## Purpose
Establish standardized Python coding practices for maintainable, readable, and robust code development.

## Core Standards

### 1. PEP 8 Style Guidelines
- **Line Length**: 79 characters maximum for code, 72 for comments
- **Naming Conventions**: snake_case for variables/functions, PascalCase for classes
- **Indentation**: 4 spaces per level (never tabs)
- **Import Organization**: standard library → third-party → local imports
- **Whitespace**: Blank lines to separate functions and classes

### 2. Type Hints and Static Analysis
- **Function Annotations**: All parameters and return types annotated
- **Optional Types**: Use `Optional[]` or `Type | None` for nullable values
- **Complex Structures**: TypedDict or dataclasses for structured data
- **MyPy Integration**: Static type checking in CI/CD pipeline
- **Generic Types**: Use `List[str]`, `Dict[str, Any]` instead of bare containers

### 3. Documentation Standards
- **Docstrings**: Google-style for all public functions, classes, modules
- **Inline Comments**: Explain complex logic and business rules
- **Type Documentation**: Document complex type definitions
- **README Files**: Comprehensive setup and usage instructions

### 4. Error Handling
- **Specific Exceptions**: Use specific exception types, avoid bare `except:`
- **Exception Chaining**: Use `raise...from` for proper error context
- **Context Managers**: Use `with` statements for resource management
- **Logging**: Structured logging instead of print statements

### 5. Code Organization
- **Modular Design**: Single responsibility principle for functions/classes
- **Package Structure**: Proper `__init__.py` files and module organization
- **Configuration**: Environment variables for settings, not hardcoded values
- **Separation of Concerns**: Clear boundaries between different functionalities

## Development Workflow

### Type Checking Configuration
```ini
[mypy]
python_version = 3.13
warn_return_any = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
warn_redundant_casts = True
warn_unused_ignores = True
strict_equality = True
```

### Testing Standards
- **Framework**: Use pytest for all testing
- **Coverage**: Maintain 90%+ coverage for critical code paths
- **Test Organization**: Mirror source structure in test directories
- **Mocking**: Mock external dependencies and I/O operations
- **Fixtures**: Use pytest fixtures for test data and setup

### Dependency Management
- **Virtual Environments**: Always use venv, conda, or poetry
- **Version Pinning**: Pin exact versions in production requirements
- **Separation**: Separate dev and production dependencies
- **Security**: Regular updates with safety or similar tools

## Quality Assurance

### Pre-commit Hooks
- **Black**: Code formatting
- **Ruff**: Fast linting and import sorting
- **MyPy**: Static type checking
- **Pytest**: Automated test execution

### Code Review Checklist
- All functions have type hints and docstrings
- No bare `except:` clauses or global variables
- Proper error handling with specific exceptions
- Tests cover new functionality
- MyPy passes without errors

### Performance Guidelines
- **List Comprehensions**: Prefer over explicit loops where readable
- **Generator Expressions**: Use for memory-efficient iteration
- **Built-in Functions**: Leverage map, filter, any, all appropriately
- **String Operations**: Use join() for concatenation in loops

## Common Anti-Patterns to Avoid

### Type-Related Issues
- Using `Any` without justification
- Missing None checks for Optional types
- Bare containers without element types
- Incorrect generic usage

### Code Structure Issues
- Global variables and mutable default arguments
- Circular imports between modules
- Deep nesting (prefer early returns)
- Large functions (keep under 20 lines when possible)

### Error Handling Issues
- Catching all exceptions with bare `except:`
- Not logging exceptions properly
- Ignoring return values from important functions
- Not cleaning up resources properly

## Gradual Adoption Strategy

### Phase 1: New Code Standards
- Add type hints to all new functions
- Use modern Python features (f-strings, pathlib)
- Implement proper error handling patterns

### Phase 2: Tool Integration
- Enable MyPy on new modules
- Add pre-commit hooks for formatting
- Integrate testing into CI/CD pipeline

### Phase 3: Legacy Code Improvement
- Gradually add types to existing critical modules
- Refactor large functions and classes
- Improve test coverage incrementally

### Phase 4: Full Enforcement
- Enforce type checking on entire codebase
- Strict linting rules for all code
- Comprehensive documentation requirements

## Quality Metrics

### Tracking Standards
- **Type Coverage**: Aim for 80%+ on new code
- **Test Coverage**: Maintain 90%+ for critical paths
- **MyPy Errors**: Track reduction over time
- **Code Complexity**: Monitor with radon or similar tools

### Success Indicators
- Reduced runtime type errors (AttributeError, TypeError)
- Faster code review cycles
- Improved IDE support and autocomplete
- Better onboarding experience for new developers

## Version History

- v1.0 (2026-01-12): Initial version based on PEP 8, type hints research, and industry best practices
