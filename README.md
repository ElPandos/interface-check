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
- **Log analysis tools** for post-processing

## Architecture

```
interface-check/
├── src/
│   ├── app.py              # Main application entry point
│   ├── core/
│   │   ├── connect/        # SSH connection management
│   │   ├── traffic/        # Traffic testing components
│   │   ├── scanner/        # Data collection workers
│   │   ├── config/         # Configuration models
│   │   ├── parser/         # Data parsers
│   │   └── log/            # Logging setup and rotation
│   ├── interfaces/         # Abstract interfaces and protocols
│   ├── models/             # Data models (Pydantic)
│   ├── platform/           # Platform-specific tools
│   │   ├── tools/          # Network tools (ethtool, mlx, mst, etc.)
│   │   └── enums/          # Platform enumerations
│   └── ui/                 # Web UI components and handlers
│       ├── tabs/           # Individual tab implementations
│       ├── handlers/       # Business logic handlers
│       ├── components/     # Reusable UI components
│       └── themes/         # UI styling and themes
├── logs/                   # Application logs and CSV outputs
├── main.py                 # Interface monitoring tool
├── main_scan.py            # Interface scanning tool
├── main_scan_analyze.py    # Log analysis tool
├── main_scan_traffic.py    # Traffic testing tool
├── main_scan_cfg.json      # Interface scanning configuration
└── main_scan_traffic_cfg.json # Traffic testing configuration
```

### Key Components

#### Core (`src/core/`)
- **connect/**: SSH and local connection management with multi-hop support
- **traffic/iperf/**: Iperf server, client, and web monitoring
- **scanner/**: SLX and SUT scanning workers with real-time data collection
- **config/**: Configuration models and validation for scan and traffic modes
- **parser/**: Data parsers for SLX and SUT output processing
- **log/**: Centralized logging with rotation and formatting

#### Platform (`src/platform/`)
- **tools/**: Network diagnostic tools (ethtool, mlx, mst, rdma, system)
- **hardware.py**: Hardware information collection
- **health.py**: System health monitoring
- **statistics.py**: Network statistics gathering
- **software_manager.py**: Package management (apt/yum)

#### UI (`src/ui/`)
- **gui.py**: Main GUI controller and window management
- **tabs/**: Individual tab implementations (host, agent, chat, system, etc.)
- **handlers/**: Business logic for UI interactions
- **components/**: Reusable UI components like connection selectors
- **themes/**: UI styling and theme management

## Quick Start

### Installation

```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Configuration

The project uses individual configuration files for each tool:

- `main_scan_cfg.json` - Interface scanning configuration
- `main_scan_traffic_cfg.json` - Traffic testing configuration

See [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) for detailed configuration instructions.

### Running

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

## Development

### Environment Setup

```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Code Quality

```bash
# Format and lint code
uv run ruff format .
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
- Direct and multi-hop connections through jump hosts
- Automatic keepalive and reconnection
- Connection pooling and status tracking
- Graceful error handling and recovery

### Network Tools Integration
- **ethtool**: Interface statistics and configuration
- **mlxlink**: Mellanox link diagnostics and eye scan data
- **mlxconfig**: Mellanox adapter configuration
- **mst**: Mellanox Software Tools integration
- **rdma**: RDMA interface monitoring
- **system**: General system information

### Interface Monitoring (`main.py`)
- Web-based GUI with real-time data visualization
- Interactive controls for connection management
- Dynamic configuration loading
- Live log viewing and analysis

### Interface Scanning (`main_scan.py`)
- Automated SLX switch port scanning with eye scan automation
- SUT (System Under Test) monitoring with configurable components
- Background worker threads with queue-based communication
- Configurable sampling intervals and skip flags
- Thread-safe data processing with automatic reconnection

### Traffic Testing (`main_scan_traffic.py`)
- **Bidirectional iperf testing**: Forward and reverse traffic flows
- **Multiple interfaces**: Test multiple IP pairs simultaneously
- **Infinite duration mode**: Background clients with periodic stats collection
- **Web monitoring UI**: Real-time process and bandwidth monitoring
- **Per-interface statistics**: Track bandwidth for each port separately
- **CSV export**: Periodic stats and summary files
- **Configurable parameters**: Bandwidth, streams, protocols, duration

### Log Analysis (`main_scan_analyze.py`)
- Post-processing of collected CSV data
- Statistical analysis and performance trends
- Error pattern detection and reporting

### Web-based GUI
- **Tabbed interface**: Organized workflow with specialized tabs
- **Real-time updates**: Live data visualization with Plotly
- **Connection status**: Visual indicators for SSH health
- **Interactive controls**: Start/stop operations, configuration changes
- **Log viewing**: Real-time log display with filtering
- **Theme support**: Customizable UI themes

## Configuration

See [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) for detailed configuration instructions.

### Main Configuration Files
- `main_scan_cfg.json` - Interface scanning configuration
- `main_scan_traffic_cfg.json` - Traffic testing configuration

### Key Settings
- Connection type (local/remote) and components to run
- Server/client hosts, IPs, ports, protocols, duration
- Web UI settings including poll rate and themes
- Logging levels and output directories

## Output Files

### Interface Check
- `logs/YYYYMMDD_HHMMSS/*.log` - Detailed execution logs
- `logs/YYYYMMDD_HHMMSS/*_info.log` - System information
- `logs/YYYYMMDD_HHMMSS/*_stats.csv` - Network statistics

### Traffic Testing
- `logs/YYYYMMDD_HHMMSS/traffic_stats.csv` - Periodic bandwidth statistics
- `logs/YYYYMMDD_HHMMSS/traffic_summary.csv` - Overall test summary
- `logs/YYYYMMDD_HHMMSS/traffic_metadata.csv` - Test configuration
- `logs/YYYYMMDD_HHMMSS/traffic.log` - Detailed execution log

### Log Analysis
- Processed CSV files with statistical analysis
- Performance trend reports
- Error pattern detection and reporting

## Technology Stack

- **Python 3.13**: Latest Python with modern type hints
- **NiceGUI 2.24.2**: Web-based GUI framework
- **Paramiko 4.0.0+**: SSH client library
- **Pydantic**: Data validation and settings management
- **Plotly 6.5.0+**: Interactive data visualization
- **Pandas 2.3.3+**: Data manipulation and analysis
- **PSUtil 7.1.0+**: System monitoring utilities

## Development Tools

- **UV**: Modern Python package manager
- **Ruff**: Fast Python linter and formatter
- **MyPy**: Static type checker
- **Pytest**: Testing framework with coverage

## License

See LICENSE file for details.
