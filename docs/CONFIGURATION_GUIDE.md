# Configuration Guide

## Overview

This guide covers configuration for the Interface Check project's multiple execution modes:

1. **Interface Monitoring** (`main.py`) - Web-based GUI for network interface monitoring
2. **Interface Scanning** (`main_scan.py`) - Automated interface scanning and data collection
3. **Traffic Testing** (`main_scan_traffic.py`) - Iperf traffic generation and monitoring
4. **Log Analysis** (`main_scan_analyze.py`) - Post-processing and analysis of collected data

## Host Configuration

The Interface Check project uses individual configuration files for each tool:

- `main_scan_cfg.json` - Interface scanning configuration
- `main_scan_traffic_cfg.json` - Traffic testing configuration

Each configuration file contains its own host connection details.

## Interface Monitoring Configuration (`main.py`)

The web-based GUI loads configuration dynamically and provides interactive controls for:

- Connection management and status monitoring
- Real-time data visualization  
- Tool execution and parameter adjustment
- Log viewing and analysis

Host connections are configured through the web interface or can reference the JSON configuration files.

## Interface Scanning Configuration (`main_scan_cfg.json`)

Controls automated scanning behavior for `main_scan.py`:

```json
{
  "log_level": "info",
  "log_rotation_timeout_sec": 120,
  "worker_collect": false,
  "jump": {
    "host": "137.58.231.134",
    "user": "emvekta",
    "pass": "emvekta"
  },
  "slx": {
    "host": "172.16.171.1",
    "user": "admin",
    "pass": "password",
    "sudo_pass": "fibranne",
    "scan_ports": ["0/9:1"],
    "scan_interval_sec": 20,
    "port_toggle_limit": 5,
    "port_toggle_wait_sec": 5,
    "port_eye_scan_wait_sec": 20
  },
  "sut": {
    "host": "172.16.225.1",
    "user": "hts",
    "pass": "hts",
    "sudo_pass": "hts",
    "scan_interfaces": ["ens3f0np0"],
    "connect_type": "remote",
    "show_parts": ["no_slx_dsc", "no_mlxlink", "no_mlxlink_amber", "no_mtemp", "no_sys_info"],
    "time_cmd": true,
    "reload_driver": false,
    "required_software_packages": [
      "pciutils", "ethtool", "rdma-core", "ibverbs-utils", 
      "lshw", "lm-sensors", "python3-pip", "mstflint"
    ],
    "scan_interval_low_res_ms": 500,
    "scan_interval_high_res_ms": 20,
    "scan_interval_tx_errors_ms": 50,
    "scan_max_log_size_kb": 20
  }
}
```

### Jump Host Configuration
- **`host`**: Jump host IP address
- **`user`**: Jump host username  
- **`pass`**: Jump host password

### SLX Switch Configuration
- **`host`**: SLX switch IP address
- **`user`**: SSH username for SLX switch
- **`pass`**: SSH password
- **`sudo_pass`**: Sudo password for privileged operations
- **`scan_ports`**: List of ports to scan (format: "slot/port:subport")
- **`scan_interval_sec`**: Interval between scans
- **`port_toggle_limit`**: Maximum number of port toggles
- **`port_toggle_wait_sec`**: Wait time between port toggles
- **`port_eye_scan_wait_sec`**: Wait time for eye scan completion

### SUT (System Under Test) Configuration
- **`host`**: SUT host IP address
- **`user`**: SSH username
- **`pass`**: SSH password
- **`sudo_pass`**: Sudo password for privileged operations
- **`scan_interfaces`**: List of network interfaces to monitor
- **`connect_type`**: Connection method ("remote" or "local")
- **`show_parts`**: Array of components to SKIP
- **`time_cmd`**: Enable command timing
- **`reload_driver`**: Enable driver reload functionality
- **`required_software_packages`**: List of required system packages
- **`scan_interval_low_res_ms`**: Low resolution scan interval (milliseconds)
- **`scan_interval_high_res_ms`**: High resolution scan interval (milliseconds)
- **`scan_interval_tx_errors_ms`**: TX error scan interval (milliseconds)
- **`scan_max_log_size_kb`**: Maximum log file size (kilobytes)

### Available Skip Flags
- `"no_slx_dsc"` - Skip SLX DSC operations
- `"no_mlxlink"` - Skip mlxlink worker (network metrics)
- `"no_mlxlink_amber"` - Skip mlxlink amber operations
- `"no_mtemp"` - Skip mget_temp worker (NIC temperature)
- `"no_sys_info"` - Skip system information collection

## Traffic Testing Configuration (`main_scan_traffic_cfg.json`)

Controls iperf traffic testing for `main_scan_traffic.py`:

```json
{
  "log_level": "info",
  "jump": {
    "host": "137.58.231.134",
    "user": "emvekta",
    "pass": "emvekta"
  },
  "server": {
    "host": "172.16.226.1",
    "user": "hts",
    "pass": "hts",
    "sudo_pass": "hts",
    "connect_type": "remote",
    "server_ip": [
      "10.101.225.30",
      "10.102.225.31", 
      "10.103.225.60",
      "10.104.225.61"
    ]
  },
  "client": {
    "host": "172.16.225.1",
    "user": "hts",
    "pass": "hts",
    "sudo_pass": "hts",
    "connect_type": "remote",
    "server_ip": [
      "10.101.226.30",
      "10.102.226.31",
      "10.103.226.60", 
      "10.104.226.61"
    ]
  },
  "setup": {
    "start_port": 5001,
    "protocol": "tcp",
    "bandwidth": "10G",
    "parallel_streams": 2,
    "stats_poll_sec": 1,
    "traffic_duration_sec": 0
  },
  "web": {
    "enabled": true,
    "port": 8080,
    "poll_rate_ms": 2000
  }
}
```

### Jump Host Configuration
- **`host`**: Jump host IP address
- **`user`**: Jump host username
- **`pass`**: Jump host password

### Server/Client Configuration
- **`host`**: SSH host to connect to
- **`user`**: SSH username
- **`pass`**: SSH password
- **`sudo_pass`**: Sudo password for privileged operations
- **`connect_type`**: Connection method ("remote" or "local")
- **`server_ip`**: List of IP addresses for iperf servers/targets

### Traffic Setup Parameters
- **`start_port`**: Starting port number (increments for each pair)
- **`protocol`**: Traffic protocol ("tcp" or "udp")
- **`bandwidth`**: Target bandwidth for UDP (e.g., "10G", "1G")
- **`parallel_streams`**: Number of parallel iperf streams per client
- **`stats_poll_sec`**: Iperf reporting interval
- **`traffic_duration_sec`**: Test duration (0 = infinite)

### Web Monitoring Configuration
- **`enabled`**: Enable web-based monitoring UI
- **`port`**: Web server port
- **`poll_rate_ms`**: UI refresh rate in milliseconds

## Configuration Examples

### Local Development Setup
```json
{
  "sut": {
    "connect_type": "local",
    "show_parts": ["no_slx_dsc", "no_sys_info"]
  }
}
```
Runs tools locally, skipping SLX DSC operations and system info collection.

### Remote Production Monitoring
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": []
  },
  "slx": {
    "scan_interval_sec": 10,
    "port_toggle_limit": 10
  }
}
```
Full remote monitoring with faster scan intervals and more port toggles.

### Minimal Link Monitoring
```json
{
  "sut": {
    "connect_type": "remote",
    "show_parts": [
      "no_sys_info",
      "no_mlxlink", 
      "no_mlxlink_amber",
      "no_mtemp",
      "no_slx_dsc"
    ]
  }
}
```
Minimal monitoring configuration.

### High-Bandwidth Traffic Testing
```json
{
  "setup": {
    "protocol": "tcp",
    "bandwidth": "100G",
    "parallel_streams": 8,
    "traffic_duration_sec": 60
  }
}
```
TCP traffic test with 8 parallel streams for 60 seconds.

## Output Configuration

### Log Directory Structure
```
logs/YYYYMMDD_HHMMSS/
├── interface_check.log     # Main application log
├── ssh_connections.log     # SSH connection details
├── network_stats.csv       # Network interface statistics
├── system_info.log         # System information
├── traffic_stats.csv       # Traffic test statistics
├── traffic_summary.csv     # Traffic test summary
└── traffic_metadata.csv    # Traffic test configuration
```

### CSV Output Format
- **Timestamps**: ISO 8601 format with timezone
- **Metrics**: Numerical values with units
- **Status**: String indicators for connection/test status
- **Metadata**: Configuration and environment information

## Environment Variables

### Optional Environment Variables
- **`INTERFACE_CHECK_LOG_LEVEL`**: Override default log level
- **`INTERFACE_CHECK_CONFIG_DIR`**: Custom configuration directory
- **`INTERFACE_CHECK_LOG_DIR`**: Custom log output directory

### SSH Configuration
- **`SSH_TIMEOUT`**: SSH connection timeout (default: 30 seconds)
- **`SSH_KEEPALIVE`**: SSH keepalive interval (default: 60 seconds)
- **`SSH_MAX_RETRIES`**: Maximum connection retry attempts (default: 3)

## Troubleshooting

### Common Configuration Issues

#### SSH Connection Failures
- Verify host IP addresses and credentials
- Check network connectivity to target hosts
- Ensure SSH service is running on target hosts
- Validate jump host configuration if using multi-hop

#### Tool Execution Failures
- Verify required tools are installed on target systems
- Check user permissions for tool execution
- Ensure sudo access if required for privileged operations
- Validate network interface names and availability

#### Web UI Issues
- Check port availability (default 8080)
- Verify firewall settings allow web access
- Ensure browser supports modern JavaScript features
- Check console for JavaScript errors

### Debug Configuration
```json
{
  "log_level": "debug",
  "sampling": {
    "interval_sec": 5
  },
  "web": {
    "poll_rate_ms": 1000
  }
}
```
Enables verbose logging and faster refresh rates for debugging.

## Migration Guide

### From Version 0.1.x to Current
1. Configuration files are now in project root:
   - `main_scan_cfg.json` - Interface scanning configuration
   - `main_scan_traffic_cfg.json` - Traffic testing configuration
2. Update `main_scan_cfg.json` structure:
   - Add `jump` host configuration section
   - Update `slx` section with detailed scan parameters
   - Add `required_software_packages` to `sut` section
   - Update `show_parts` values to current options
3. Ensure `main_scan_traffic_cfg.json` has jump host configuration
4. Add log rotation timeout and worker collection settings

### Configuration Validation
The application validates configuration on startup and provides detailed error messages for:
- Missing required fields
- Invalid parameter values
- Conflicting configuration options
- Network connectivity issues

Run with `--validate-config` flag to check configuration without starting services.
