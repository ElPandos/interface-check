# .amazonq/rules/python-standards.md
# Python Optimization Rules
## Goals
- Fix all runtime & syntax errors.
- Enforce type hints, docstrings, and code comments.
- Ensure async-safe, secure, and maintainable patterns.
- Use reproducible execution (e.g., virtualenvs or tools like uv).
- Align linting, typing, and testing with shared dependencies.

## Execution
- Run scripts in isolated environments for reproducibility.
- Example: Use `uv run <file.py>` or `python -m venv` for testing.
