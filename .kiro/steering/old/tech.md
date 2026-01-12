---
title: Interface Check - Technology Stack
inclusion: always
---

# Interface Check - Technology Stack

## Programming Language
- **Python 3.13**: Latest Python version with modern type hints and performance improvements

## Core Dependencies
- **NiceGUI 2.24.2**: Web-based GUI framework for Python applications
- **Paramiko 4.0.0+**: SSH client library for remote connections
- **Pydantic**: Data validation and settings management
- **Plotly 6.3.1+**: Interactive data visualization and charting
- **Pandas 2.3.3+**: Data manipulation and analysis
- **PSUtil 7.1.0+**: System and process monitoring utilities

## Development Tools
- **UV**: Modern Python package manager and virtual environment tool
- **Ruff**: Fast Python linter and formatter (replaces flake8, isort, black)
- **Black**: Code formatter for consistent styling (deprecated - use ruff format)
- **MyPy**: Static type checker with strict configuration
- **Pre-commit**: Git hooks for code quality enforcement
- **Pytest**: Testing framework with coverage reporting

## Build & Deployment
- **Docker**: Containerization with multi-stage builds
- **Docker Compose**: Local development environment orchestration
- **GitHub Actions**: CI/CD pipeline for linting and testing
- **Taskfile**: Task runner for common development commands

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run application
uv run main.py
```

### Code Quality
```bash
# Format code
uv run black .
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .

# Run tests
uv run pytest
```

### Docker Operations
```bash
# Build and run
docker-compose up --build

# Development mode
docker-compose -f docker-compose.yml up
```

## Configuration
- **pyproject.toml**: Project metadata, dependencies, and tool configurations
- **Ruff**: Comprehensive linting with ALL rules enabled, specific ignores
- **MyPy**: Strict type checking with Python 3.13 target
- **Black**: 120 character line length, Python 3.13 target