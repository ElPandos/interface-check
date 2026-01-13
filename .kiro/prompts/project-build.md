---
title:        Project Build Instructions
inclusion:    always
version:      1.3
last-updated: 2026-01-13
status:       active
---

# Project Build Instructions

## Quick Start
```bash
# Setup and run
uv sync && uv run main.py
```

## Development Setup

### Prerequisites
- UV package manager
- Python 3.13+

### Environment
```bash
# Install dependencies
uv sync

# Activate environment (optional - uv run handles this)
source .venv/bin/activate
```

## Applications

```bash
# Interface monitoring (web GUI)
uv run main.py

# Interface scanning
uv run main_scan.py

# Traffic testing
uv run main_scan_traffic.py

# Log analysis
uv run main_scan_analyze.py
```

## Code Quality

```bash
# Format + lint (combined)
uv run ruff format . && uv run ruff check --fix .

# Type check
uv run mypy .

# Test with coverage
uv run pytest --cov=src
```

## Binary Builds

Build standalone executables with PyInstaller:

```bash
# Interface check binary
uv run pyinstaller interop_check.spec --clean

# Traffic testing binary
uv run pyinstaller interop_traffic.spec --clean
```

Output: `dist/` directory

## Version History

- v1.0 (2026-01-12): Initial version
- v1.2 (2026-01-12): Removed reference to missing build_binary.sh script
- v1.3 (2026-01-13): Streamlined structure, added quick start, combined commands
