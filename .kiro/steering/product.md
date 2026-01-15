---
title:        Product Foundation
inclusion:    always
version:      1.1
last-updated: 2026-01-15 16:20:00
status:       active
---

# Product Foundation

## Vision
Enterprise-grade network interface monitoring and traffic testing tool enabling engineers to diagnose, monitor, and validate high-performance network infrastructure through SSH-based remote management with interactive web GUI.

## Problem Statement
Network engineers need to:
- Monitor interface health across distributed systems without direct access
- Diagnose Mellanox/NVIDIA NIC issues through multi-hop SSH connections
- Automate eye scan and DSC diagnostics for signal integrity analysis
- Perform bidirectional iperf traffic testing with detailed per-interface statistics
- Analyze historical data for trend detection and troubleshooting
- Manage system health monitoring (temperature, power, hardware info)
- Execute platform-specific tools remotely (ethtool, mlxlink, mlxconfig, mst, rdma)

## Target Users
- **Network Engineers**: Primary users performing diagnostics and monitoring
- **System Administrators**: Managing remote infrastructure via jump hosts
- **QA Engineers**: Running traffic tests and collecting performance data
- **DevOps Teams**: Automating network validation in CI/CD pipelines
- **Hardware Engineers**: Analyzing signal integrity and hardware health

## Core Capabilities

### 1. Remote Diagnostics
- SSH-based tool execution (ethtool, mlxlink, mlxconfig, mst, rdma, dmesg)
- Multi-hop connections through jump hosts
- Local and remote execution modes
- Automatic reconnection and keepalive

### 2. Interface Monitoring
- Real-time statistics collection (bandwidth, errors, drops)
- Hardware information (vendor, model, firmware)
- Health metrics (temperature, power consumption)
- RDMA interface monitoring

### 3. SLX Switch Automation
- Automated eye scan execution on configured ports
- DSC (Digital Signal Conditioning) diagnostics
- Port state management (up/down toggling)
- Interface caching for performance

### 4. SUT System Monitoring
- Configurable component scanning (mlxlink, temperature, system info)
- Concurrent monitoring with SLX operations
- Flap detection and state tracking
- CSV logging for analysis

### 5. Traffic Testing
- Iperf3-based bidirectional throughput validation
- TCP and UDP protocol support
- Multiple parallel streams
- Per-interface bandwidth statistics
- Web-based monitoring UI

### 6. Web Interface
- NiceGUI-based reactive dashboard
- Tabbed interface (Host, Local, SLX, System, Agent, Chat, etc.)
- Real-time data visualization with Plotly
- Interactive controls and configuration
- Theme support (light/dark mode)

### 7. Data Collection & Analysis
- Automated scanning with configurable intervals
- CSV export for historical analysis
- Log rotation and management
- Post-processing tools for trend detection

## Key Workflows

### Interface Monitoring
1. Configure hosts and routes in JSON config
2. Launch web GUI (`main.py`)
3. Select target host and interfaces
4. View real-time statistics and health metrics
5. Export data for analysis

### Automated Scanning
1. Configure SLX ports and SUT interfaces in `main_scan_cfg.json`
2. Run scanner (`main_scan.py`)
3. Monitor eye scan and system metrics collection
4. Review CSV logs for analysis

### Traffic Testing
1. Configure server/client hosts in `main_scan_traffic_cfg.json`
2. Run traffic tool (`main_scan_traffic.py`)
3. Monitor bandwidth via web UI
4. Analyze CSV statistics

### Log Analysis
1. Collect historical CSV data
2. Run analyzer (`main_scan_analyze.py`)
3. Generate reports and identify patterns

## Success Metrics
- Connection reliability through multi-hop SSH
- Data collection completeness and accuracy
- Traffic test throughput validation
- Time-to-diagnosis for network issues
- System uptime and stability
- User workflow efficiency

## Version History

- v1.0 (2026-01-14 12:47:00): Initial product foundation
- v1.1 (2026-01-15 16:20:00): Updated with current capabilities, workflows, and architecture
