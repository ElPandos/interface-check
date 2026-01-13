---
title:        Project Build Instructions
inclusion:    always
version:      1.2
last-updated: 2026-01-12
status:       active
---

# Project Build Instructions

## Development Setup

### Prerequisites
- UV package manager installed
- Python 3.13+ available

### Environment Setup
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Running Applications
```bash
# Interface monitoring with web GUI
uv run main.py

# Interface scanning
uv run main_scan.py

# Traffic testing with iperf
uv run main_scan_traffic.py

# Log analysis
uv run main_scan_analyze.py
```

## Code Quality

### Formatting and Linting
```bash
# Format code
uv run ruff format .

# Lint and fix issues
uv run ruff check . --fix

# Type checking
uv run mypy .
```

### Testing
```bash
# Run tests with coverage
uv run pytest --cov=src
```

## Binary Build Process

Build standalone executables using PyInstaller.

### Build Commands

#### Interface Check Binary
```bash
uv run pyinstaller interop_check.spec --clean
```

#### Traffic Testing Binary
```bash
uv run pyinstaller interop_traffic.spec --clean
```

Executables are generated in the `dist/` directory.

## Version History

- v1.0 (2026-01-12): Initial version
- v1.2 (2026-01-12): Removed reference to missing build_binary.sh script
