---
title: Traffic Testing Patterns
inclusion: fileMatch
fileMatchPattern: 'src/core/traffic/**/*.py,main_scan_traffic.py'
---

# Traffic Testing Patterns

## Iperf Management
- **Server Lifecycle**: Start/stop iperf servers with proper cleanup
- **Client Management**: Manage multiple concurrent iperf clients
- **Process Monitoring**: Track iperf process health and resource usage
- **Port Management**: Dynamic port allocation and conflict resolution

## Bidirectional Testing
- **Forward Traffic**: Client to server traffic flows
- **Reverse Traffic**: Server to client traffic flows
- **Simultaneous Testing**: Run both directions concurrently
- **Result Correlation**: Match forward and reverse test results

## Bandwidth Monitoring
- **Real-time Statistics**: Live bandwidth and throughput monitoring
- **Per-interface Tracking**: Monitor bandwidth for each network interface
- **Aggregated Metrics**: Total bandwidth across all interfaces
- **Historical Data**: Store and analyze bandwidth trends over time

## Test Configuration
- **Protocol Support**: TCP and UDP traffic testing
- **Parallel Streams**: Multiple concurrent streams per test
- **Duration Control**: Finite and infinite duration tests
- **Bandwidth Limiting**: Target bandwidth configuration for UDP

## Data Collection
- **Statistics Parsing**: Parse iperf output for bandwidth data
- **CSV Export**: Export test results to CSV format
- **Metadata Tracking**: Store test configuration and environment info
- **Error Handling**: Handle iperf failures and partial results

## Web Monitoring
- **Real-time UI**: Live traffic monitoring dashboard
- **Process Status**: Visual indicators for running tests
- **Control Interface**: Start/stop tests from web interface
- **Log Streaming**: Real-time log display in web UI

## Performance Optimization
- **Resource Management**: Monitor CPU and memory usage during tests
- **Network Utilization**: Track network interface utilization
- **Concurrent Limits**: Limit concurrent tests to prevent overload
- **Cleanup Procedures**: Proper cleanup of test processes and resources
