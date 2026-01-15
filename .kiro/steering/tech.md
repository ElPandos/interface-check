---
title:        Technology Foundation
inclusion:    always
version:      1.1
last-updated: 2026-01-15 16:20:00
status:       active
---

# Technology Foundation

## Runtime Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.13 | Core runtime with modern type hints |
| NiceGUI | 2.24.2 | Web-based GUI (FastAPI + Vue.js) |
| Paramiko | 4.0.0+ | SSH client for remote connections |
| Pydantic | 2.12+ | Data validation and configuration |
| Plotly | 6.5+ | Interactive data visualization |
| Pandas | 2.3+ | Data manipulation and analysis |
| PSUtil | 7.2+ | System monitoring utilities |

## Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| UV | Package manager | `pyproject.toml` |
| Ruff | Linter/formatter | line-length: 120 |
| MyPy | Type checker | strict mode |
| Pytest | Testing | with coverage |

## Key Dependencies

### SSH & Networking
- `paramiko>=4.0.0`: Multi-hop SSH connections with keepalive
- `psutil>=7.2.1`: System and network interface monitoring

### Web UI
- `nicegui==2.24.2`: Reactive web interface with Quasar components
- `plotly>=6.5.1`: Real-time charts and graphs

### Data Handling
- `pydantic>=2.12.5`: Configuration models with SecretStr for passwords
- `pydantic-settings>=2.12.0`: Settings management
- `pandas>=2.3.3`: CSV export and data analysis

### Utilities
- `python-dotenv>=1.2.1`: Environment variable management
- `keyboard>=0.13.5`: Keyboard input handling
- `pympler>=1.1`: Memory profiling

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, tool configs |
| `main_scan_cfg.json` | Interface scanning settings |
| `main_scan_traffic_cfg.json` | Traffic testing settings |

## Code Standards

- **Type hints**: Required everywhere with `from __future__ import annotations`
- **Docstrings**: Google-style for public classes and methods
- **Line length**: 120 characters max
- **Imports**: Grouped (stdlib, third-party, local) and alphabetically sorted
- **Error handling**: Comprehensive try-catch with structured logging

## Ruff Configuration

### Selected Rules
- All rules enabled by default (`ALL`)
- Specific ignores for documentation, complexity, and framework-specific rules
- Google-style docstring convention
- Strict type checking with flake8-type-checking

### Key Settings
```toml
line-length = 120
target-version = "py313"
fixable = ["ALL"]
```

## MyPy Configuration

```toml
python_version = "3.13"
strict = true
```

## Commands

```bash
# Development
uv sync                    # Install dependencies
source .venv/bin/activate  # Activate venv

# Quality
uv run ruff format .       # Format code
uv run ruff check . --fix  # Lint code
uv run mypy .              # Type check
uv run pytest --cov=src    # Run tests with coverage

# Run
uv run main.py             # Web GUI
uv run main_scan.py        # Interface scanning
uv run main_scan_traffic.py # Traffic testing
uv run main_scan_analyze.py # Log analysis
```

## Version History

- v1.0 (2026-01-14 00:00:00): Initial technology foundation
- v1.1 (2026-01-15 16:20:00): Updated dependencies, added utilities, expanded configuration details
