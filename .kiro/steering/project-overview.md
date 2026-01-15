---
title:        Interface Check Project Overview
inclusion:    always
version:      1.0
last-updated: 2026-01-14 13:12:00
status:       active
---

# Interface Check Project Overview

## Purpose
Network interface monitoring and traffic testing tool with SSH-based remote management and web-based GUI. Provides real-time diagnostics for network interfaces on remote systems via SSH.

## Technology Stack

### Core Technologies
- **Python 3.13**: Latest Python with modern type hints
- **NiceGUI 2.24.2**: Web-based GUI framework (FastAPI + Vue.js)
- **Paramiko 4.0.0+**: SSH client library for remote connections
- **Pydantic 2.12+**: Data validation and settings management
- **Plotly 6.5+**: Interactive data visualization
- **Pandas 2.3+**: Data manipulation and analysis

### Development Tools
- **UV**: Modern Python package manager
- **Ruff**: Fast Python linter and formatter (line-length: 120)
- **MyPy**: Static type checker (strict mode)
- **Pytest**: Testing framework with coverage

## Architecture Overview

```
interface-check/
├── src/
│   ├── app.py              # Main application entry point
│   ├── core/               # Core business logic
│   │   ├── connect/        # SSH and local connection management
│   │   ├── traffic/        # Traffic testing (iperf)
│   │   ├── scanner/        # Data collection workers (SLX, SUT)
│   │   ├── config/         # Configuration models
│   │   ├── parser/         # Data parsers (SLX, SUT output)
│   │   └── log/            # Logging setup and rotation
│   ├── interfaces/         # Abstract interfaces and protocols
│   ├── models/             # Pydantic data models
│   ├── platform/           # Platform-specific tools
│   │   ├── tools/          # Network tools (ethtool, mlx, mst)
│   │   └── enums/          # Platform enumerations
│   └── ui/                 # Web UI components
│       ├── tabs/           # Individual tab implementations
│       ├── handlers/       # Business logic handlers
│       ├── components/     # Reusable UI components
│       └── themes/         # UI styling
├── main.py                 # Interface monitoring tool
├── main_scan.py            # Interface scanning tool
├── main_scan_traffic.py    # Traffic testing tool
└── main_scan_analyze.py    # Log analysis tool
```

## Key Components

### Connection Management (`src/core/connect/`)
- **SshConnection**: Multi-hop SSH with jump host support, keepalive, reconnection
- **LocalConnection**: Local command execution wrapper
- **IConnection**: Abstract interface for connection types

### Network Tools (`src/platform/tools/`)
- **ethtool**: Interface statistics and configuration
- **mlxlink**: Mellanox link diagnostics and eye scan
- **mst**: Mellanox Software Tools integration
- **rdma**: RDMA interface monitoring
- **system**: General system information

### Scanner Workers (`src/core/scanner/`)
- **SlxScanner**: SLX switch port scanning with eye scan automation
- **SutScanner**: System Under Test monitoring with configurable components
- Background worker threads with queue-based communication

### Web UI (`src/ui/`)
- **Gui**: Main controller managing tabs and panels
- **Tab classes**: LocalTab, HostTab, SlxTab, SystemTab, etc.
- **Handlers**: Business logic separation from UI components
- **Themes**: Centralized styling with apply_global_theme()

## Configuration

### Main Configuration Files
- `main_scan_cfg.json`: Interface scanning configuration
- `main_scan_traffic_cfg.json`: Traffic testing configuration

### Pydantic Models (`src/models/config.py`)
- **Host**: IP, username, password, info
- **Route**: Connection path through multiple hosts
- **Settings**: Application options (debug, dark mode, intervals)
- **Config**: Root configuration combining all settings

## Entry Points

| Script | Purpose |
|--------|---------|
| `main.py` | Interface monitoring with web GUI |
| `main_scan.py` | Automated interface scanning |
| `main_scan_traffic.py` | Iperf traffic testing |
| `main_scan_analyze.py` | Log analysis and post-processing |

## Code Standards

### Type Hints
- Required for all functions and methods
- Use `from __future__ import annotations` for forward references
- Strict MyPy compliance

### Documentation
- Google-style docstrings for public classes and methods
- Module-level docstrings describing purpose

### Error Handling
- Comprehensive try-catch with logging
- Graceful degradation for connection failures
- Automatic reconnection for SSH sessions

### Logging
- Structured logging with LogName enums
- Rotation and formatting via `src/core/log/`
- Debug, info, warning, error levels

## Development Workflow

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Format and lint
uv run ruff format .
uv run ruff check . --fix

# Type check
uv run mypy .

# Run tests
uv run pytest --cov=src
```

## Version History

- v1.0 (2026-01-14 00:00:00): Initial project overview based on codebase analysis
