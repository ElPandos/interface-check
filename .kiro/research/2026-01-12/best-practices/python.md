# Research Output – 2026-01-12 23:49 CET

## Original Prompt
> Research best python practices. Use the research file to create/update .kiro/steering/python_best-practices.md

## Complete Response

Based on comprehensive research of current industry practices, here are the essential Python best practices for 2025:

### Core Language Features and Modern Python

**Python 3.13+ Features**:
- **Type Hints**: Mandatory for all functions and methods - Facebook's 2025 survey shows growing adoption for improved code quality and flexibility
- **Dataclasses**: Use for structured data with automatic method generation
- **Async/Await**: Essential for I/O-bound operations with up to 400% performance improvements in high-concurrency environments
- **Pattern Matching**: Use match/case statements for complex conditional logic
- **Walrus Operator**: Use := for assignment expressions in comprehensions and conditions

**Type System Excellence**:
- Use `from __future__ import annotations` for forward references
- Prefer built-in generics (`list[str]`) over typing module equivalents in Python 3.9+
- Use Protocol classes for structural typing
- Implement proper generic types with TypeVar
- Use Union types and Optional for nullable values

### Code Quality and Tooling

**Modern Tooling Stack (2025)**:
- **Ruff**: Fast linter and formatter replacing Black, isort, and flake8
- **MyPy**: Static type checker with strict mode enabled
- **Pytest**: Testing framework with fixtures and parametrization
- **Pre-commit**: Automated code quality checks before commits
- **UV**: Modern package manager for faster dependency resolution

**Code Formatting Standards**:
- Line length: 88 characters (Black default) or 120 for modern projects
- Use trailing commas in multi-line structures
- Prefer f-strings over .format() or % formatting
- Use pathlib.Path instead of os.path for file operations
- Follow PEP 8 naming conventions strictly

### Performance Optimization

**Concurrency and Parallelism**:
- **AsyncIO**: First choice for I/O-bound applications (web servers, API clients)
- **Multiprocessing**: For CPU-bound tasks to overcome GIL limitations
- **Threading**: For I/O-bound tasks with blocking operations
- **Concurrent.futures**: High-level interface for parallel execution

**Memory Management**:
- Use generators and iterators for large datasets
- Implement __slots__ for memory-critical classes
- Use weak references to break circular references
- Profile memory usage with tools like memory_profiler
- Prefer list comprehensions over map/filter for readability

**Performance Best Practices**:
- Use built-in functions and libraries (NumPy, Pandas) for heavy computation
- Cache expensive operations with functools.lru_cache
- Use sets for membership testing instead of lists
- Prefer collections.deque for queue operations
- Use string.join() for concatenating multiple strings

### Testing and Quality Assurance

**Testing Strategy**:
- **Unit Tests**: 70% of test suite using pytest with fixtures
- **Integration Tests**: 20% testing component interactions
- **End-to-End Tests**: 10% testing complete user workflows
- **Property-Based Testing**: Use Hypothesis for edge case discovery
- **Test Coverage**: Aim for 80%+ meaningful coverage

**Testing Best Practices**:
- Use pytest fixtures for test setup and teardown
- Parametrize tests to cover multiple scenarios
- Mock external dependencies with unittest.mock
- Use pytest-asyncio for testing async code
- Implement proper test isolation and cleanup

### Security and Best Practices

**Security Considerations**:
- Validate all input data using Pydantic or similar libraries
- Use secrets module for cryptographically secure random numbers
- Avoid eval() and exec() functions
- Use environment variables for sensitive configuration
- Implement proper error handling without exposing internal details

**Dependency Management**:
- Pin exact versions in production (requirements.txt or pyproject.toml)
- Use virtual environments for all projects
- Regular security audits with tools like safety or pip-audit
- Keep dependencies minimal and up-to-date
- Use dependabot or similar for automated updates

### Modern Development Patterns

**Project Structure**:
```
project/
├── src/
│   └── package/
│       ├── __init__.py
│       ├── main.py
│       └── modules/
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── .pre-commit-config.yaml
```

**Configuration Management**:
- Use Pydantic Settings for configuration validation
- Environment-based configuration with .env files
- Separate configuration for different environments
- Use dataclasses or Pydantic models for structured config

**Error Handling**:
- Use specific exception types instead of generic Exception
- Implement proper logging with structured formats
- Use context managers for resource management
- Fail fast with clear error messages
- Implement retry mechanisms with exponential backoff

### Async Programming Excellence

**AsyncIO Best Practices**:
- Use async/await for I/O-bound operations
- Implement proper connection pooling for HTTP clients
- Use asyncio.gather() for concurrent operations
- Handle cancellation gracefully with try/except
- Use asyncio.create_task() for fire-and-forget operations

**Async Patterns**:
- Producer-consumer patterns with asyncio.Queue
- Rate limiting with asyncio.Semaphore
- Timeout handling with asyncio.wait_for()
- Background tasks with asyncio.create_task()
- Proper cleanup with async context managers

### Documentation and Maintainability

**Documentation Standards**:
- Use Google-style or NumPy-style docstrings
- Type hints serve as inline documentation
- Maintain README with setup and usage instructions
- Use Sphinx for API documentation generation
- Include examples in docstrings

**Code Organization**:
- Follow single responsibility principle
- Use dependency injection for testability
- Implement proper separation of concerns
- Use factory patterns for complex object creation
- Keep functions small and focused (under 20 lines)

## Key Findings

- **Type hints are becoming mandatory**: Facebook's 2025 survey shows widespread adoption for code quality
- **Ruff is replacing multiple tools**: Single tool for linting, formatting, and import sorting
- **AsyncIO performance gains**: Up to 400% improvement in high-concurrency environments
- **Modern tooling ecosystem**: UV, Ruff, and improved type checkers are standard
- **GIL removal progress**: Python's Global Interpreter Lock limitations being addressed
- **Testing-first culture**: Comprehensive testing with pytest and property-based testing

## Sources & References

- [2025 Python Year in Review - Talk Python](https://talkpython.fm/episodes/show/532/2025-python-year-in-review) — Current Python ecosystem trends - accessed 2026-01-12
- [Facebook Typed Python Survey](https://www.infoq.com/news/2026/01/facebook-typed-python-survey/) — Type hints adoption and benefits - accessed 2026-01-12
- [Clean Code in Python 2nd Edition](https://www.clcoding.com/2026/01/clean-code-in-python-develop.html) — Modern Python development practices - accessed 2026-01-12
- [Master Asynchronous Programming](https://moldstud.com/articles/p-master-asynchronous-programming-in-python-a-step-by-step-optimization-guide) — AsyncIO performance optimization - accessed 2026-01-12
- [Python Concurrency Best Practices](https://python-academy.org/en/guide/concurrency-best-practices) — Concurrency patterns and recommendations - accessed 2026-01-12

## Tools & Methods Used

- web_search: "Python best practices 2025 coding standards PEP 8 type hints modern development"
- web_search: "Python 3.13 best practices 2025 type hints dataclasses async await modern patterns"
- web_search: "Python code quality best practices 2025 linting formatting black ruff mypy testing pytest"
- web_search: "Python performance optimization 2025 profiling memory management concurrency asyncio best practices"

## Metadata

- Generated: 2026-01-12T23:49:22+01:00
- Model: Claude 3.5 Sonnet
- Tags: python, best-practices, type-hints, asyncio, performance, testing, code-quality
- Confidence: High - Based on current industry research and established Python practices
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Python ecosystem evolves rapidly; tool recommendations may change
- Performance optimizations depend on specific use cases and requirements
- Some advanced patterns require Python 3.9+ features
- Regular review of emerging tools and practices recommended
