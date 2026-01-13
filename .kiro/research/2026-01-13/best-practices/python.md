# Research Output – 2026-01-13 00:44 CET

## Original Prompt
> Research best python practices. Use the research file to create/update .kiro/steering/python_best-practices.md

## Complete Response

Based on comprehensive research of current Python development practices in 2025-2026, here are the essential best practices for modern Python development:

## Modern Python Tooling Revolution

The Python ecosystem has undergone a significant transformation with new Rust-based tools providing dramatic performance improvements:

### Package Management Evolution
- **UV**: The new standard for Python package management, written in Rust, offering 10-100x faster installations than pip
- **Poetry 2.0**: Enhanced with better performance and plugin hooks for structured projects
- **pyproject.toml**: Universal configuration standard replacing setup.py

### Code Quality Trinity
- **Ruff**: Extremely fast linter and formatter (written in Rust), replacing Flake8, isort, and other tools
- **Black**: Uncompromising code formatter for consistent style
- **Mypy**: Static type checking for catching type-related errors

## Core Development Principles

### Type Safety and Modern Python
- **Type Hints**: Mandatory for all functions and methods in professional projects
- **Static Type Checking**: Use Mypy to catch type-related errors before runtime
- **Modern Python Features**: Leverage Python 3.10+ features like pattern matching and union types

### Code Organization and Structure
- **PEP 8 Compliance**: Follow Python's official style guide consistently
- **Modular Design**: Organize code into logical, reusable modules
- **Single Responsibility**: Each function and class should have one clear purpose
- **Meaningful Names**: Use descriptive names that explain purpose without comments

### Dependency Management
- **Virtual Environments**: Always use isolated environments (venv, Poetry, or UV)
- **Lock Files**: Use lock files for reproducible builds
- **Dependency Scanning**: Regular vulnerability assessments with tools like Safety or Snyk
- **Minimal Dependencies**: Only include necessary packages to reduce attack surface

## Asynchronous Programming Best Practices

### Modern Async Patterns
- **async/await Syntax**: Use modern async syntax for better readability
- **Event Loop Management**: Understand and optimize event loop performance
- **Non-blocking Operations**: Avoid blocking operations in async code
- **Concurrent Task Management**: Use asyncio.gather() and asyncio.create_task() effectively

### Performance Optimization
- **I/O Bound Tasks**: Use asyncio for I/O-bound operations (can improve responsiveness by 50%)
- **CPU Bound Tasks**: Use multiprocessing for CPU-intensive work to overcome GIL limitations
- **Connection Pooling**: Implement connection pooling for database and HTTP clients
- **Async Context Managers**: Use async with for proper resource management

## Security Best Practices

### Secrets Management
- **Environment Variables**: Store secrets in environment variables, never in code
- **Secret Vaults**: Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
- **Credential Rotation**: Implement automatic credential rotation
- **Least Privilege**: Grant minimum necessary permissions

### Input Validation and Security
- **Input Sanitization**: Validate and sanitize all user inputs
- **SQL Injection Prevention**: Use parameterized queries and ORMs
- **Dependency Scanning**: Regular vulnerability scans with tools like Bandit and Safety
- **Security Headers**: Implement proper security headers in web applications

## Testing Excellence

### Testing Strategy
- **Test-Driven Development**: Write tests before implementation when appropriate
- **Pytest Framework**: Use pytest as the standard testing framework
- **Test Coverage**: Aim for meaningful coverage of critical code paths (80%+ target)
- **Test Independence**: Each test should run independently without dependencies

### Modern Testing Approaches
- **Property-Based Testing**: Use Hypothesis for generating test cases automatically
- **Contract Testing**: Verify API contracts between services
- **Parameterized Tests**: Test multiple scenarios efficiently with pytest.mark.parametrize
- **Fixture Management**: Use pytest fixtures for test setup and teardown

## Performance Optimization

### Profiling and Monitoring
- **Profile First**: Use cProfile, line_profiler, or py-spy to identify bottlenecks
- **Memory Profiling**: Use memory_profiler to track memory usage
- **Structured Logging**: Implement structured logging with JSON format
- **Application Monitoring**: Use APM tools like New Relic or Datadog

### Optimization Techniques
- **Algorithm Selection**: Choose efficient algorithms and data structures
- **Caching Strategies**: Implement appropriate caching at multiple levels
- **Database Optimization**: Optimize queries, indexing, and connection pooling
- **Just-in-Time Compilation**: Use Numba for CPU-intensive numerical computations

## Modern Development Workflow

### CI/CD Integration
- **Automated Testing**: Run comprehensive test suites on every change
- **Code Quality Gates**: Integrate Ruff, Black, and Mypy in CI/CD pipelines
- **Security Scanning**: Automated vulnerability scanning in deployment pipelines
- **Deployment Automation**: Use containerization and infrastructure as code

### Documentation and Maintenance
- **Docstrings**: Use Google-style or NumPy-style docstrings consistently
- **API Documentation**: Generate documentation from code annotations
- **README Files**: Clear setup, usage, and contribution instructions
- **Changelog**: Document all significant changes and version history

## Key Findings

- **Tooling Revolution**: Rust-based tools (UV, Ruff) provide 10-100x performance improvements over traditional Python tools
- **Type Safety**: Static type checking with Mypy has become essential for professional Python development
- **Async Adoption**: Proper async programming can improve application responsiveness by up to 50% for I/O-bound tasks
- **Security Focus**: Dependency scanning and secrets management are now critical requirements, not optional practices
- **Testing Maturity**: Modern testing approaches with pytest, property-based testing, and contract testing are becoming standard

## Sources & References

- [Python Best Practices: The 2025 Guide for Clean, Fast, and Secure Code](https://nerdleveltech.com/python-best-practices-the-2025-guide-for-clean-fast-and-secure-code) — Comprehensive modern practices guide
- [Python Best Practices to Follow in 2026](https://www.geekcafe.com/blog/2025/12/python-best-practices-for-2026) — Latest tooling and practices
- [Modern Good Practices for Python Development](https://www.stuartellis.name/articles/python-modern-practices/) — Development environment best practices
- [Python UV: The Ultimate Guide to the Fastest Python Package Manager](https://www.datacamp.com/tutorial/python-uv) — Modern package management
- [Advanced Python Concurrency: Asyncio Event Loop Optimization](https://dhirendrabiswal.com/advanced-python-concurrency-asyncio-event-loop-optimization-and-concurrent-futures-patterns/) — Async programming patterns
- [Python Security Best Practices](https://databytesandinsights.substack.com/p/day-48-of-50-days-of-python-python) — Security practices
- [Testing in Python with Pytest: A Complete Guide](https://obedmacallums.com/posts/testing-python-pytest) — Modern testing approaches

## Tools & Methods Used

- web_search: "Python best practices 2025 2026 modern development standards"
- web_search: "Python modern tooling 2025 uv ruff mypy poetry packaging best practices"
- web_search: "Python async programming best practices 2025 asyncio performance patterns"
- web_search: "Python security best practices 2025 dependency scanning secrets management"
- web_search: "Python testing best practices 2025 pytest coverage modern testing strategies"

## Metadata

- Generated: 2026-01-13T00:44:47+01:00
- Model: Claude 3.5 Sonnet
- Tags: python, best-practices, modern-tooling, security, testing, async, performance
- Confidence: High - Based on current industry research and established practices
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Practices may evolve as Python ecosystem continues rapid development
- Tool recommendations based on current performance benchmarks and adoption trends
- Security practices should be regularly updated as threat landscape evolves
