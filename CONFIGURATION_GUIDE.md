# Configuration Guide

## Overview

This guide covers configuration for both:
1. **Interface Check** (`main.py`) - Network interface monitoring
2. **Traffic Testing** (`main_scan_traffic.py`) - Iperf traffic generation and monitoring

## Interface Check Configuration

The interface check tool uses two independent settings to control behavior:

1. **`connect_type`** - Determines how to connect to the SUT (System Under Test)
2. **`show_parts`** - List of components to SKIP (empty = run everything)

## Connection Type

Controls the connection method to the SUT:

```json
"connect_type": "local"   // Run commands locally on the SUT machine
"connect_type": "remote"  // Run commands via SSH to the SUT
```

### Local Mode
- Runs all workers: mlxlink, mget_temp, dmesg
- Executes commands directly on the local machine
- No SSH connection needed

### Remote Mode
- Runs all workers: mlxlink, mget_temp, dmesg
- Executes commands via SSH to the remote SUT
- Requires MST tools installed on remote machine

## Show Parts (Skip Flags)

An array of components to SKIP. **Empty array = run everything.**

Available skip flags:
- `"no_sys_info"` - Skip system information collection at startup
- `"no_mlxlink"` - Skip mlxlink worker (network metrics)
- `"no_mtemp"` - Skip mget_temp worker (NIC temperature)
- `"no_dmesg"` - Skip dmesg worker (link flap detection)
- `"no_eye_scan"` - Skip SLX eye scan automation

## Configuration Examples

### Run Everything Locally
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": []
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg + eye_scan (all locally)

### Run Locally, Skip Eye Scan
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": ["no_eye_scan"]
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg

### Run Locally, Only Monitor Link Flaps
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": ["no_sys_info", "no_mlxlink", "no_mtemp", "no_eye_scan"]
  }
}
```
**Runs:** dmesg only

### Run Remotely (SSH)
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": []
  }
}
```
**Runs:** sys_info + mlxlink + mget_temp + dmesg + eye_scan (all via SSH)

### Run Remotely, Skip Everything Except Dmesg
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": ["no_sys_info", "no_eye_scan"]
  }
}
```
**Runs:** dmesg only

## Port Toggling

Port toggling is controlled by the SLX configuration and only works when eye scanning is enabled:

```json
{
  "slx": {
    "port_toggling_enabled": true,
    "port_toggle_wait_sec": 5
  },
  "sut": {
    "show_parts": []  // Must NOT include "no_eye_scan"
  }
}
```

**Important:** Port toggling requires eye scanning to be active. If `"no_eye_scan"` is in `show_parts`, port toggling will not occur.

## Migration from Old Config

### Old Format (DEPRECATED)
```json
{
  "connect_type": "remote",
  "show_parts": ["remote", "no_eye_scan"]  // ❌ Don't use "remote" or "local" here
}
```

### New Format (CORRECT)
```json
{
  "connect_type": "remote",
  "show_parts": ["no_eye_scan"]  // ✅ Only skip flags
}
```

## Traffic Testing Configuration

The traffic testing tool (`main_scan_traffic.py`) uses a separate configuration file (`main_scan_traffic_cfg.json`).

### Basic Structure

```json
{
  "log_level": "info",
  "jump": { /* Jump host for SSH */ },
  "server": { /* Server host configuration */ },
  "client": { /* Client host configuration */ },
  "setup": { /* Traffic test parameters */ },
  "web": { /* Web UI settings */ }
}
```

### Server Configuration

```json
"server": {
  "host": "172.16.226.1",
  "user": "hts",
  "pass": "hts",
  "sudo_pass": "hts",
  "connect_type": "remote",
  "server_ip": ["10.101.225.30", "10.102.225.31", "10.103.225.60", "10.104.225.61"]
}
```

- **`host`** - SSH host to connect to
- **`server_ip`** - List of IPs to bind iperf servers to (one server per IP)
- **`connect_type`** - `"remote"` for SSH, `"local"` for local execution

### Client Configuration

```json
"client": {
  "host": "172.16.225.1",
  "user": "hts",
  "pass": "hts",
  "sudo_pass": "hts",
  "connect_type": "remote",
  "server_ip": ["10.101.226.30", "10.102.226.31", "10.103.226.60", "10.104.226.61"]
}
```

- **`server_ip`** - List of target IPs for iperf clients (one client per IP)

### Traffic Setup

```json
"setup": {
  "start_port": 5001,
  "protocol": "tcp",
  "bandwidth": "10G",
  "parallel_streams": 2,
  "stats_poll_sec": 1,
  "traffic_duration_sec": 0
}
```

- **`start_port`** - Starting port number (increments for each server/client pair)
- **`protocol`** - `"tcp"` or `"udp"`
- **`bandwidth`** - Target bandwidth for UDP (e.g., `"10G"`, `"1G"`)
- **`parallel_streams`** - Number of parallel iperf streams per client
- **`stats_poll_sec`** - Iperf reporting interval in seconds
- **`traffic_duration_sec`** - Test duration (0 = infinite)

### Web UI Configuration

```json
"web": {
  "enabled": true,
  "port": 8080,
  "poll_rate_ms": 2000
}
```

- **`enabled`** - Enable/disable web monitoring UI
- **`port`** - Web server port
- **`poll_rate_ms`** - UI refresh rate in milliseconds (default: 2000ms)

### Traffic Test Modes

#### Finite Duration Test
```json
"setup": {
  "traffic_duration_sec": 30
}
```
- Clients run for 30 seconds and return statistics
- Statistics written to CSV after completion

#### Infinite Duration Test
```json
"setup": {
  "traffic_duration_sec": 0
}
```
- Clients run continuously in background
- Statistics collected from log files and written to CSV every 5 seconds
- Use web UI or Ctrl+C to terminate

### Output Files

All files are created in `logs/YYYYMMDD_HHMMSS/`:

- **`traffic_stats.csv`** - Periodic bandwidth statistics (updated every 5s for infinite tests)
  - Columns: timestamp, total bandwidth, per-interface bandwidth
- **`traffic_summary.csv`** - Overall test summary (updated every 5s for infinite tests)
  - Columns: avg/max/min bandwidth, samples, duration, per-interface stats
- **`traffic_metadata.csv`** - Test configuration metadata
- **`traffic.log`** - Detailed execution log

### Web UI Features

- **Real-time process monitoring** - Shows running iperf servers and clients
- **Live bandwidth statistics** - Current, average, maximum bandwidth
- **Per-interface tracking** - Bandwidth per port/interface
- **Traffic log** - Real-time log messages
- **Terminate button** - Gracefully stop all traffic tests

## Summary

### Interface Check (main.py)
- **`connect_type`** = HOW to execute commands (local vs SSH)
  - Both modes run all workers (mlxlink, mget_temp, dmesg)
  - Remote mode requires MST tools on the remote machine
- **`show_parts`** = WHAT to skip (empty = skip nothing)
- **Port toggling** = Requires eye scan to be enabled (no `"no_eye_scan"` flag)

### Traffic Testing (main_scan_traffic.py)
- **Bidirectional testing** - Forward (client→server) and reverse (server→client)
- **Multiple interfaces** - Test multiple IP pairs simultaneously
- **Infinite duration** - Background mode with periodic CSV updates
- **Web monitoring** - Real-time UI with configurable refresh rate
- **Per-interface stats** - Track bandwidth for each port separately
