# Iperf Traffic Testing

Automated iperf traffic testing with SSH-based remote execution and comprehensive statistics collection.

## Features

- **Remote Execution**: Run iperf server and client on remote hosts via SSH
- **Protocol Support**: TCP and UDP traffic testing
- **Configurable Parameters**: Duration, bandwidth, parallel streams, iterations
- **CSV Logging**: Statistics saved in CSV format for easy analysis with plotly
- **Graceful Shutdown**: Ctrl+C handling with proper cleanup
- **Multi-hop SSH**: Support for jump hosts

## Quick Start

### 1. Configuration

Edit `main_scan_traffic_cfg.json`:

```json
{
    "log_level": "info",
    "jump": {
        "host": "jump.example.com",
        "user": "username",
        "pass": "password"
    },
    "server": {
        "host": "192.168.1.100",
        "user": "user",
        "pass": "pass",
        "sudo_pass": "pass",
        "port": 5201,
        "connect_type": "remote"
    },
    "client": {
        "host": "192.168.1.101",
        "user": "user",
        "pass": "pass",
        "sudo_pass": "pass",
        "connect_type": "remote"
    },
    "test": {
        "duration_sec": 30,
        "protocol": "tcp",
        "bandwidth": "10G",
        "parallel_streams": 1,
        "interval_sec": 1,
        "iterations": 5,
        "delay_between_tests_sec": 5
    }
}
```

### 2. Run Tests

```bash
python main_scan_traffic.py
```

### 3. Analyze Results

Results are saved to `logs/<timestamp>/traffic_stats.csv` with columns:
- `iteration`: Test iteration number
- `timestamp`: Sample timestamp
- `interval`: Time interval
- `transfer_bytes`: Bytes transferred
- `bandwidth_bps`: Bandwidth in bits/second
- `bandwidth_mbps`: Bandwidth in Mbits/second
- `bandwidth_gbps`: Bandwidth in Gbits/second
- `jitter_ms`: Jitter in milliseconds (UDP only)
- `lost_packets`: Lost packets (UDP only)
- `total_packets`: Total packets (UDP only)
- `loss_percent`: Packet loss percentage (UDP only)

## Architecture

### Class Hierarchy

```
IperfBase (abstract)
├── IperfServer
└── IperfClient
```

### IperfBase

Common functionality for server and client:
- Connection management (SSH or Local)
- Output parsing
- Statistics collection
- Process management

### IperfServer

Server-specific methods:
- `start(daemon=True)`: Start iperf server
- `stop()`: Graceful shutdown
- `kill()`: Force kill
- `is_running()`: Check server status

### IperfClient

Client-specific methods:
- `configure(duration, protocol, bandwidth, parallel)`: Set test parameters
- `start()`: Run test and collect statistics
- `get_stats()`: Retrieve collected statistics

## Configuration Options

### Connection Types

- `remote`: SSH connection through jump host
- `local`: Local command execution (no SSH)

### Test Parameters

- **duration_sec**: Test duration in seconds
- **protocol**: `tcp` or `udp`
- **bandwidth**: Target bandwidth for UDP (e.g., "1G", "100M")
- **parallel_streams**: Number of parallel streams
- **interval_sec**: Reporting interval in seconds
- **iterations**: Number of test runs
- **delay_between_tests_sec**: Delay between iterations
- **bidir**: Run bidirectional test (simultaneous send/receive)
- **reverse**: Run reverse mode (server sends to client)

## Example Usage

### TCP Throughput Test

```json
"test": {
    "duration_sec": 60,
    "protocol": "tcp",
    "parallel_streams": 4,
    "iterations": 10,
    "interval_sec": 1
}
```

### UDP Bandwidth Test

```json
"test": {
    "duration_sec": 30,
    "protocol": "udp",
    "bandwidth": "10G",
    "iterations": 5,
    "interval_sec": 1
}
```

### Bidirectional Test

```json
"test": {
    "duration_sec": 30,
    "protocol": "tcp",
    "bidir": true,
    "interval_sec": 1
}
```

### Reverse Mode Test

```json
"test": {
    "duration_sec": 30,
    "protocol": "tcp",
    "reverse": true,
    "interval_sec": 1
}
```

## Visualization

Use plotly to visualize results:

```python
import pandas as pd
import plotly.express as px

df = pd.read_csv("logs/<timestamp>/traffic_stats.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Bandwidth over time
fig = px.line(df, x="timestamp", y="bandwidth_gbps", color="iteration",
              title="Bandwidth Over Time")
fig.show()

# Packet loss (UDP)
if "loss_percent" in df.columns:
    fig = px.scatter(df, x="timestamp", y="loss_percent", color="iteration",
                     title="Packet Loss Over Time")
    fig.show()
```

## Troubleshooting

### Server Won't Start

- Check if port is already in use: `netstat -tulpn | grep 5001`
- Verify iperf is installed: `which iperf`
- Check firewall rules

### Connection Failures

- Verify SSH credentials in config
- Test manual SSH connection
- Check jump host connectivity

### No Statistics Collected

- Check iperf output format
- Verify test duration is sufficient
- Review logs in `logs/<timestamp>/main.log`

## Requirements

- Python 3.10+
- iperf installed on both server and client hosts
- SSH access to remote hosts
- Network connectivity between hosts
