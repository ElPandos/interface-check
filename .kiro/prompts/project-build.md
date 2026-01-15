---
title:        Project Build Instructions
inclusion:    always
version:      1.4
last-updated: 2026-01-15 16:26:00
status:       active
---

# Project Build Instructions

## Quick Start
```bash
# Setup and run web GUI
uv sync && uv run main.py
```

## Development Setup

### Prerequisites
- UV package manager (latest)
- Python 3.13+
- Linux or macOS

### Environment
```bash
# Install all dependencies
uv sync

# Activate environment (optional - uv run handles this)
source .venv/bin/activate
```

## Applications

### Main Tools
```bash
# Interface monitoring (NiceGUI web interface)
uv run main.py

# Interface scanning (SLX eye scan + SUT monitoring)
uv run main_scan.py

# Traffic testing (iperf with web monitoring)
uv run main_scan_traffic.py

# Log analysis (CSV post-processing)
uv run main_scan_analyze.py
```

### Configuration Files
- `main_scan_cfg.json` - Interface scanning settings
- `main_scan_traffic_cfg.json` - Traffic testing settings

## Code Quality

### Formatting & Linting
```bash
# Format code (line-length: 120)
uv run ruff format .

# Lint and auto-fix
uv run ruff check --fix .

# Combined format + lint
uv run ruff format . && uv run ruff check --fix .
```

### Type Checking
```bash
# Strict type checking
uv run mypy .
```

### Testing
```bash
# Run tests with coverage
uv run pytest --cov=src

# Generate HTML coverage report
uv run pytest --cov=src --cov-report=html
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

## Project Structure

```
interface-check/
├── src/                    # Source code
│   ├── app.py             # Application entry
│   ├── core/              # Business logic
│   ├── interfaces/        # Abstract interfaces
│   ├── models/            # Pydantic models
│   ├── platform/          # Platform-specific tools
│   └── ui/                # Web UI components
├── main*.py               # Entry points
├── tests/                 # Test suite
├── pyproject.toml         # Project configuration
└── .kiro/                 # Kiro CLI configuration
```

## Dependencies

### Core Runtime
- Python 3.13
- NiceGUI 2.24.2 (web UI)
- Paramiko 4.0.0+ (SSH)
- Pydantic 2.12+ (validation)
- Plotly 6.5+ (visualization)
- Pandas 2.3+ (data analysis)
- PSUtil 7.2+ (system monitoring)

### Development
- Ruff (linter/formatter)
- MyPy (type checker)
- Pytest (testing)
- PyInstaller 6.18+ (binary builds)

## Version History

- v1.0 (2026-01-12 00:00:00): Initial version
- v1.2 (2026-01-12 00:00:00): Removed reference to missing build_binary.sh script
- v1.3 (2026-01-13 00:00:00): Streamlined structure, added quick start, combined commands
- v1.4 (2026-01-15 16:26:00): Added configuration files, project structure, dependencies, expanded testing section
