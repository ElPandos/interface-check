# Interface Check

Network interface monitoring and diagnostic tool with SSH-based remote management and web-based GUI.

## Overview

Interface Check provides real-time monitoring and diagnostics for network interfaces on remote systems via SSH. It features:

- **Multi-hop SSH connections** through jump hosts
- **Web-based GUI** built with NiceGUI
- **Network tool integration** (ethtool, mlxlink, mlxconfig, mst)
- **Real-time data collection** with worker threads
- **Eye scan automation** for SLX switches
- **System health monitoring** for SUT (System Under Test)

## Architecture

```
interface-check/
├── src/
│   ├── core/          # Core functionality (SSH, workers, parsers)
│   ├── interfaces/    # Abstract interfaces and protocols
│   ├── models/        # Data models (Pydantic)
│   ├── platform/      # Platform-specific tools and utilities
│   └── ui/            # Web UI components and handlers
├── config/            # Configuration files
├── logs/              # Application logs
└── main_eye_scan.py   # Standalone eye scan automation
```

### Key Components

#### Core (`src/core/`)
- **connect.py**: SSH connection management with multi-hop support
- **worker.py**: Background thread workers for data collection
- **parser.py**: Output parsers for network tools (mlxlink, ethtool, etc.)
- **sample.py**: Data sample collection and storage

#### Platform (`src/platform/`)
- **hardware.py**: Hardware information collection
- **health.py**: System health monitoring
- **statistics.py**: Network statistics gathering
- **software_manager.py**: Package management (apt/yum)

#### UI (`src/ui/`)
- **gui.py**: Main GUI controller
- **tabs/**: Individual tab implementations
- **handlers/**: Business logic for UI interactions
- **components/**: Reusable UI components

## Quick Start

### Installation

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Configuration

Edit `config/config.json` with your SSH connection details:

```json
{
  "hosts": [
    {
      "ip": "192.168.1.100",
      "username": "admin",
      "password": "secret",
      "jump": false
    }
  ]
}
```

### Running

```bash
# Web GUI
uv run main.py

# Eye scan automation (standalone)
uv run main_eye_scan.py
```

## Development

### Compile binary

```bash
pyinstaller \
    --onefile \
    --clean \
    --noconfirm \
    --name interop_check \
    main_eye_scan.py
```

### Code Quality

```bash
# Format code
uv run black .
uv run ruff format .

# Lint
uv run ruff check . --fix

# Type check
uv run mypy .

# Run tests
uv run pytest --cov=src
```

### Project Standards

- **Type hints**: Required for all functions and methods
- **Docstrings**: Google-style for all public classes and methods
- **Error handling**: Comprehensive try-catch with logging
- **Line length**: 120 characters max
- **Logging**: Structured logging with appropriate levels

## Features

### SSH Connection Management
- Direct and multi-hop connections
- Automatic keepalive
- Connection pooling
- Graceful reconnection

### Network Tools
- **ethtool**: Interface statistics and configuration
- **mlxlink**: Mellanox link diagnostics
- **mlxconfig**: Mellanox adapter configuration
- **mst**: Mellanox Software Tools integration

### Data Collection
- Background worker threads
- Configurable sampling intervals
- Thread-safe queue-based communication
- Automatic reconnection on failures

### Eye Scan Automation
- SLX switch integration
- Port toggling support
- Configurable scan intervals
- Result logging and export

## License

See LICENSE file for details.
