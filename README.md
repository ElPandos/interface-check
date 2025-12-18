# Interface Check

Network interface monitoring and traffic testing tool with SSH-based remote management and web-based GUI.

## Overview

Interface Check provides real-time monitoring, diagnostics, and traffic testing for network interfaces on remote systems via SSH. It features:

- **Multi-hop SSH connections** through jump hosts
- **Web-based GUI** built with NiceGUI
- **Network tool integration** (ethtool, mlxlink, mlxconfig, mst)
- **Real-time data collection** with worker threads
- **Eye scan automation** for SLX switches
- **System health monitoring** for SUT (System Under Test)
- **Iperf traffic testing** with bidirectional support
- **Live traffic monitoring** with per-interface statistics

## Architecture

```
interface-check/
├── src/
│   ├── core/
│   │   ├── connect/        # SSH connection management
│   │   ├── traffic/        # Traffic testing (iperf)
│   │   │   └── iperf/      # Iperf server/client/monitor
│   │   ├── scanner/        # SLX and SUT scanners
│   │   └── config/         # Configuration models
│   ├── interfaces/         # Abstract interfaces and protocols
│   ├── models/             # Data models (Pydantic)
│   ├── platform/           # Platform-specific tools
│   └── ui/                 # Web UI components and handlers
├── config/                 # Configuration files
├── logs/                   # Application logs and CSV outputs
├── main.py                 # Interface monitoring tool
├── main_scan.py            # Interface scanning tool
└── main_scan_traffic.py    # Traffic testing tool
```

### Key Components

#### Core (`src/core/`)
- **connect/**: SSH and local connection management with multi-hop support
- **traffic/iperf/**: Iperf server, client, and web monitoring
  - **base.py**: Common iperf functionality
  - **server.py**: Iperf server management
  - **client.py**: Iperf client management
  - **gui.py**: Web-based traffic monitoring UI
- **scanner/**: SLX and SUT scanning workers
- **config/**: Configuration models and validation

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
# Interface monitoring with web GUI
uv run main.py

# Interface scanning
uv run main_scan.py

# Traffic testing with iperf
uv run main_scan_traffic.py
```

## Development



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

### Traffic Testing
- **Bidirectional iperf testing**: Forward and reverse traffic flows
- **Multiple interfaces**: Test multiple IP pairs simultaneously
- **Infinite duration mode**: Background clients with periodic stats collection
- **Web monitoring UI**: Real-time process and bandwidth monitoring
- **Per-interface statistics**: Track bandwidth for each port separately
- **CSV export**: Periodic stats and summary files
- **Configurable poll rate**: Adjustable UI refresh rate (default: 2000ms)

## Configuration

See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for detailed configuration instructions.

### Interface Check Config
- `main_scan_cfg.json` - Interface monitoring configuration
- Controls connection type (local/remote) and components to run

### Traffic Testing Config
- `main_scan_traffic_cfg.json` - Traffic testing configuration
- Server/client hosts, IPs, ports, protocols, duration
- Web UI settings including poll rate

## Output Files

### Interface Check
- `logs/YYYYMMDD_HHMMSS/*.log` - Detailed execution logs
- `logs/YYYYMMDD_HHMMSS/*_info.log` - System information

### Traffic Testing
- `logs/YYYYMMDD_HHMMSS/traffic_stats.csv` - Periodic bandwidth statistics
- `logs/YYYYMMDD_HHMMSS/traffic_summary.csv` - Overall test summary
- `logs/YYYYMMDD_HHMMSS/traffic_metadata.csv` - Test configuration
- `logs/YYYYMMDD_HHMMSS/traffic.log` - Detailed execution log

## License

See LICENSE file for details.
