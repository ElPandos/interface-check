---
title:        Product Foundation
inclusion:    always
version:      1.0
last-updated: 2026-01-14 12:47:00
status:       active
---

# Product Foundation

## Vision
Enterprise-grade network interface monitoring and traffic testing tool enabling engineers to diagnose, monitor, and validate high-performance network infrastructure through SSH-based remote management.

## Problem Statement
Network engineers need to:
- Monitor interface health across distributed systems without direct access
- Diagnose Mellanox/NVIDIA NIC issues through multi-hop SSH connections
- Automate eye scan data collection for signal integrity analysis
- Perform bidirectional traffic testing with detailed per-interface statistics
- Analyze historical data for trend detection and troubleshooting

## Target Users
- **Network Engineers**: Primary users performing diagnostics and monitoring
- **System Administrators**: Managing remote infrastructure via jump hosts
- **QA Engineers**: Running traffic tests and collecting performance data
- **DevOps Teams**: Automating network validation in CI/CD pipelines

## Core Capabilities
1. **Remote Diagnostics**: SSH-based tool execution (ethtool, mlxlink, mst, rdma)
2. **Multi-hop Access**: Jump host chains for isolated network segments
3. **Real-time Monitoring**: Live interface statistics and health metrics
4. **Traffic Testing**: Iperf-based bidirectional throughput validation
5. **Data Collection**: Automated scanning with CSV export for analysis
6. **Web Interface**: NiceGUI-based dashboard for interactive control

## Key Workflows
- **Interface Monitoring**: Connect → Select interfaces → View real-time stats
- **Eye Scan Collection**: Configure ports → Run automated scans → Export data
- **Traffic Testing**: Setup iperf servers/clients → Monitor bandwidth → Analyze results
- **Log Analysis**: Load historical data → Identify patterns → Generate reports

## Success Metrics
- Connection reliability through jump hosts
- Data collection completeness and accuracy
- Traffic test throughput validation
- Time-to-diagnosis for network issues

## Version History

- v1.0 (2026-01-14 00:00:00): Initial product foundation
