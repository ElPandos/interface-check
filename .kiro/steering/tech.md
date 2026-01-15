---
title:        Technology Foundation
inclusion:    always
version:      1.0
last-updated: 2026-01-14 12:48:00
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
| PSUtil | 7.1+ | System monitoring utilities |

## Development Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| UV | Package manager | `pyproject.toml` |
| Ruff | Linter/formatter | line-length: 120 |
| MyPy | Type checker | strict mode |
| Pytest | Testing | with coverage |

## Key Dependencies

### SSH & Networking
- `paramiko`: Multi-hop SSH connections with keepalive
- `psutil`: System and network interface monitoring

### Web UI
- `nicegui`: Reactive web interface with Quasar components
- `plotly`: Real-time charts and graphs

### Data Handling
- `pydantic`: Configuration models with SecretStr for passwords
- `pandas`: CSV export and data analysis

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies |
| `main_scan_cfg.json` | Interface scanning settings |
| `main_scan_traffic_cfg.json` | Traffic testing settings |

## Code Standards

- **Type hints**: Required everywhere
- **Docstrings**: Google-style
- **Line length**: 120 characters
- **Imports**: `from __future__ import annotations`

## Commands

```bash
# Development
uv sync                    # Install dependencies
source .venv/bin/activate  # Activate venv

# Quality
uv run ruff format .       # Format code
uv run ruff check . --fix  # Lint code
uv run mypy .              # Type check
uv run pytest --cov=src    # Run tests

# Run
uv run main.py             # Web GUI
uv run main_scan.py        # Interface scanning
uv run main_scan_traffic.py # Traffic testing
```

## Version History

- v1.0 (2026-01-14 00:00:00): Initial technology foundation
