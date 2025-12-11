# Traffic Testing Validation Features

## Overview
Enhanced iperf traffic testing with comprehensive validation and error handling.

## New Features

### 1. Connection Validation (Ping Test)
**Location**: `IperfBase.validate_connection()`

Validates SSH connection and network reachability before starting tests.

```python
# Self-test
server.validate_connection()

# Test connectivity to target
client.validate_connection(server_host)
```

**Benefits**:
- Detects network issues early
- Prevents wasted test iterations
- Clear error messages

### 2. Port Reachability Check
**Location**: `IperfBase.check_port_reachable()`

Verifies server port is accessible from client before running tests.

```python
client.check_port_reachable(server_host, server_port)
```

**Benefits**:
- Detects firewall blocks
- Identifies routing issues
- Prevents connection refused errors

### 3. Automatic Retry Logic
**Location**: `IperfClient.start()`

Automatically retries failed tests up to 3 attempts on connection errors.

**Benefits**:
- Handles transient network issues
- Reduces false failures
- Improves test reliability

### 4. Result Validation
**Location**: `IperfBase.validate_results()`

Validates test results for anomalies:
- Zero bandwidth detection
- High packet loss detection (>10% for UDP)

```python
is_valid, error_msg = client.validate_results(stats)
```

**Benefits**:
- Detects failed tests automatically
- Identifies network degradation
- Prevents bad data in results

### 5. Progress Indication
**Location**: `main_scan_traffic.py`

Shows test progress percentage during iterations.

```
Test iteration 3/10 (Progress: 30%)
```

**Benefits**:
- User feedback during long tests
- Estimated completion visibility

## Implementation Details

### Connection Validation Flow
```
1. Connect to hosts
2. Validate server connection (ping self)
3. Validate client→server connectivity (ping)
4. Start server
5. Check port reachability (TCP connection test)
6. Run tests
```

### Retry Logic
- Max 3 attempts per test
- 2 second delay between retries
- Only retries on "Connection refused" errors
- Logs each retry attempt

### Result Validation Criteria
- **Zero bandwidth**: Any sample with 0 bps fails validation
- **High packet loss**: UDP tests with >10% loss fail validation
- **No data**: Tests with no statistics fail validation

## Error Messages

### Connection Validation
```
Cannot reach 192.168.1.100: Network is unreachable
```

### Port Reachability
```
Port 5201 on 192.168.1.100 is not reachable (firewall/network issue?)
```

### Result Validation
```
Result validation failed: Found 5 samples with zero bandwidth
Result validation failed: High packet loss detected: 15.32% avg
```

## Configuration

No additional configuration required. All validation features are enabled by default.

## Performance Impact

- Connection validation: ~3 seconds (3 ping packets)
- Port reachability: ~5 seconds (TCP connection test)
- Result validation: <1ms (in-memory check)
- Retry logic: +2 seconds per retry (max 2 retries)

Total overhead: ~8-14 seconds per test run (one-time, not per iteration)

## Troubleshooting

### Connection Validation Fails
- Check network connectivity
- Verify SSH credentials
- Check jump host configuration

### Port Not Reachable
- Verify firewall rules
- Check iptables on server
- Verify server is listening on correct port

### High Retry Count
- Check network stability
- Verify server capacity
- Reduce parallel streams

### Zero Bandwidth Results
- Check network interface status
- Verify no bandwidth limits
- Check for network congestion
