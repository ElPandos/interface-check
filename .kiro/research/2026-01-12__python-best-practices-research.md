# Research Output – 2026-01-12 13:33 CET

## Original Prompt
> Can you reasearch python best practices? and use the research file to create a .kiro/steering/python-best-practices.md file

## Complete Response

Python best practices encompass coding standards, type safety, documentation, and development workflow patterns that ensure maintainable, readable, and robust code. Based on current industry standards and PEP guidelines, here are the essential practices:

**Core Python Best Practices:**

1. **PEP 8 Style Guidelines**: Follow official Python style guide
   - Line length: 79 characters maximum for code, 72 for comments
   - Naming conventions: snake_case for variables/functions, PascalCase for classes
   - Indentation: 4 spaces per level (never tabs)
   - Import organization: standard library → third-party → local imports
   - Whitespace: blank lines to separate functions and classes

2. **Type Hints and Static Analysis**: Use Python 3.5+ type annotations
   - Function parameters and return types always annotated
   - Use Optional[] for nullable values
   - Complex data structures with TypedDict or dataclasses
   - MyPy integration for static type checking
   - Catches 15% more bugs than manual review alone

3. **Documentation Standards**: Comprehensive code documentation
   - Docstrings for all public functions, classes, and modules
   - Google-style or NumPy-style docstring format
   - Inline comments for complex logic
   - README files with setup and usage instructions

4. **Error Handling**: Robust exception management
   - Specific exception types rather than bare except clauses
   - Proper exception chaining with raise...from
   - Context managers for resource management
   - Logging instead of print statements for debugging

5. **Code Organization**: Structured project layout
   - Modular design with single responsibility principle
   - Package structure with __init__.py files
   - Separation of concerns between modules
   - Configuration management with environment variables

6. **Testing Best Practices**: Comprehensive test coverage
   - Unit tests with pytest framework
   - Test-driven development (TDD) approach
   - Mock external dependencies
   - Continuous integration with automated testing

7. **Dependency Management**: Modern package management
   - Use virtual environments (venv, conda, or poetry)
   - Pin dependency versions in requirements files
   - Separate dev and production dependencies
   - Regular security updates with tools like safety

8. **Performance Considerations**: Efficient code patterns
   - List comprehensions over loops where appropriate
   - Generator expressions for memory efficiency
   - Proper use of built-in functions (map, filter, reduce)
   - Profile code with cProfile for optimization

**Advanced Type Hint Patterns:**

- **Protocol for Duck Typing**: Define interfaces for dependency injection
- **Generic Types**: Create reusable, type-safe components
- **Literal Types**: Restrict values to specific constants
- **Union Types**: Handle multiple possible types explicitly

**MyPy Configuration Best Practices:**
```ini
[mypy]
python_version = 3.9
warn_return_any = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
warn_redundant_casts = True
warn_unused_ignores = True
strict_equality = True
```

**Common Anti-Patterns to Avoid:**
- Using `Any` type liberally without justification
- Bare `except:` clauses that catch all exceptions
- Global variables and mutable default arguments
- String concatenation in loops (use join() instead)
- Not handling None values explicitly
- Importing entire modules when only specific functions needed

**Industry Examples:**
- **Google**: Strict type checking and comprehensive docstrings
- **Instagram**: Heavy use of type hints for large-scale Python applications
- **Dropbox**: MyPy development and static analysis integration
- **Netflix**: Microservices architecture with Python best practices

**Development Workflow Integration:**
- Pre-commit hooks with black, flake8, mypy, and isort
- CI/CD pipeline with automated testing and type checking
- Code review checklists including type hint verification
- IDE integration for real-time error detection

**Gradual Adoption Strategy:**
1. **Phase 1**: Add type hints to new functions and public APIs
2. **Phase 2**: Enable MyPy on new modules with strict settings
3. **Phase 3**: Gradually add types to existing critical modules
4. **Phase 4**: Enforce type checking on entire codebase

**Quality Metrics:**
- Type coverage percentage: Aim for 80%+ on new code
- MyPy error count: Track reduction over time
- Test coverage: Maintain 90%+ for critical code paths
- Code complexity: Use tools like radon to monitor complexity

These practices ensure Python code is maintainable, scalable, and follows industry standards for professional development environments.

## Key Findings
- Type hints with MyPy static analysis catch 15% more bugs than manual review alone
- PEP 8 compliance with 79-character line limits and snake_case naming is industry standard
- Modern Python development requires virtual environments and dependency pinning
- Gradual type adoption strategy works better than attempting full coverage immediately

## Sources & References
- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/) — official Python style guidelines
- [Python Type Hints in Code Review: MyPy Integration and Best Practices](https://www.propelcode.ai/blog/python-type-hints-code-review-guide-mypy-best-practices) — comprehensive type hints guide
- [Developer Guidelines](https://devguide.trimble.com/code-style/python/) — PEP 484 type hints implementation
- [Python Development Standards for Enterprise Software](https://www.zestminds.com/blog/python-development-standards-enterprise-software/) — enterprise-level best practices

## Tools & Methods Used
- web_search: "Python best practices 2026 coding standards PEP8 type hints"
- web_fetch: https://www.propelcode.ai/blog/python-type-hints-code-review-guide-mypy-best-practices

## Metadata
- Generated: 2026-01-12T13:33:04+01:00
- Model: Claude (Kiro CLI)
- Tool calls total: 2
- Approximate duration: ~3 minutes

## Limitations & Confidence Notes
- Data current as of January 2026 – Python ecosystem continues evolving rapidly
- Type hint practices may vary based on team size and project complexity
- Recommended next steps: Implement gradual adoption strategy starting with new code
