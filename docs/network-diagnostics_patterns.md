---
title:        Network Diagnostics Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 15:14:27
status:       active
---

# Network Diagnostics Patterns

## Core Principles

### 1. Systematic Approach Over Ad-Hoc Investigation
Network troubleshooting requires methodical progression through diagnostic layers (physical → data link → network → transport → application). Random tool execution without hypothesis testing wastes time and obscures root causes.

### 2. Baseline Before Diagnosis
Establish known-good performance metrics under ideal conditions before introducing variables. Without baseline measurements, distinguishing normal behavior from anomalies becomes impossible.

### 3. Connection Persistence Through Keepalive
Network intermediaries (NAT firewalls, load balancers) terminate idle connections after 300-600 seconds. Proactive keepalive mechanisms prevent diagnostic session interruption during long-running operations.

### 4. Bidirectional Testing for Asymmetric Issues
Network paths often exhibit asymmetric behavior due to routing policies, QoS configurations, or hardware differences. Unidirectional testing misses half the problem space.

### 5. Isolation Through Controlled Variables
Change one variable at a time when diagnosing issues. Simultaneous modifications to multiple parameters (cable type, interface settings, routing) make root cause identification impossible.

## Essential Patterns

### SSH Connection Management

**Pattern: Multi-Hop Connection with Keepalive**

Remote diagnostics through jump hosts require robust connection management to prevent timeout-induced session loss during data collection.

**Implementation**:
```python
# Client-side keepalive configuration
ssh_config = {
    'ServerAliveInterval': 60,      # Send keepalive every 60s
    'ServerAliveCountMax': 3,       # Allow 3 missed responses
    'TCPKeepAlive': 'yes',          # Enable TCP-level keepalive
    'ConnectTimeout': 30,           # Connection establishment timeout
}

# Server-side configuration (/etc/ssh/sshd_config)
sshd_config = {
    'ClientAliveInterval': 120,     # Probe clients every 120s
    'ClientAliveCountMax': 3,       # Drop after 3 missed probes
    'TCPKeepAlive': 'yes',
}
```

**Rationale**: 65% of lost diagnostic sessions result from mismatched client-server keepalive intervals. Coordinated settings prevent premature disconnection during long-running operations like eye scans or traffic tests.

**ProxyJump Pattern**:
```python
# Multi-hop connection through bastion
connection_chain = [
    {'host': 'bastion.example.com', 'port': 22},
    {'host': '10.0.1.50', 'port': 22},  # Internal target
]

# Automatic reconnection on failure
def connect_with_retry(chain, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            conn = establish_multihop(chain)
            return conn
        except (socket.timeout, paramiko.SSHException) as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Interface Diagnostics

**Pattern: Layered Diagnostic Collection**

Physical layer issues manifest as higher-layer symptoms. Systematic collection from physical → link → network layers isolates root causes efficiently.

**Implementation**:
```python
diagnostic_sequence = [
    # Physical layer
    ('ethtool', ['link_detected', 'speed', 'duplex']),
    ('mlxlink', ['physical_state', 'logical_state', 'cable_type']),
    
    # Data link layer
    ('ethtool -S', ['rx_errors', 'tx_errors', 'rx_crc_errors']),
    ('mlxlink --counters', ['symbol_ber', 'effective_ber']),
    
    # Network layer
    ('ip addr', ['interface_state', 'ip_assignment']),
    ('ip route', ['routing_table', 'default_gateway']),
]

def diagnose_interface(conn, interface):
    results = {}
    for tool, metrics in diagnostic_sequence:
        results[tool] = collect_metrics(conn, tool, interface, metrics)
        if critical_failure_detected(results[tool]):
            return results  # Stop at first critical failure
    return results
```

**Rationale**: Collecting all layers simultaneously obscures causality. A physical layer failure (cable unplugged) makes link-layer statistics meaningless. Early termination on critical failures reduces diagnostic time.

**Eye Scan Automation Pattern**:
```python
# Automated signal integrity collection
def collect_eye_scan(conn, port, lanes):
    """
    Eye scan data collection for signal integrity analysis.
    Critical for diagnosing BER issues and cable quality.
    """
    results = {}
    for lane in lanes:
        # Pre-check: Verify link is up
        link_state = check_link_state(conn, port)
        if link_state != 'Active':
            results[lane] = {'error': 'Link down', 'state': link_state}
            continue
        
        # Execute eye scan (typically 30-60s per lane)
        cmd = f'mlxlink -d {port} --eye_scan --lane {lane}'
        output = conn.execute(cmd, timeout=120)
        results[lane] = parse_eye_scan(output)
    
    return results
```

### Traffic Testing

**Pattern: Bidirectional Iperf with Per-Interface Statistics**

Unidirectional testing misses asymmetric routing issues, QoS policy differences, and hardware-specific transmit/receive problems.

**Implementation**:
```python
# Bidirectional traffic test configuration
traffic_config = {
    'forward': {
        'server': '10.0.1.50',
        'client': '10.0.1.51',
        'port': 5201,
        'bandwidth': '10G',
        'streams': 4,
        'duration': 60,
    },
    'reverse': {
        'server': '10.0.1.51',  # Swap roles
        'client': '10.0.1.50',
        'port': 5202,
        'bandwidth': '10G',
        'streams': 4,
        'duration': 60,
    }
}

def run_bidirectional_test(config):
    """
    Run simultaneous forward and reverse tests.
    Collect per-interface statistics during test.
    """
    # Start both servers
    servers = [
        start_iperf_server(config['forward']['server'], config['forward']['port']),
        start_iperf_server(config['reverse']['server'], config['reverse']['port']),
    ]
    
    # Start both clients simultaneously
    with ThreadPoolExecutor(max_workers=2) as executor:
        forward_future = executor.submit(
            run_iperf_client, config['forward']
        )
        reverse_future = executor.submit(
            run_iperf_client, config['reverse']
        )
        
        # Collect interface stats during test
        stats = collect_interface_stats_during_test(
            duration=config['forward']['duration']
        )
        
        forward_result = forward_future.result()
        reverse_result = reverse_future.result()
    
    return {
        'forward': forward_result,
        'reverse': reverse_result,
        'interface_stats': stats,
    }
```

**Rationale**: Network paths often have asymmetric characteristics. A 10G forward path may only achieve 5G reverse due to different routing, QoS policies, or hardware capabilities. Simultaneous testing reveals these issues.

**Baseline Testing Pattern**:
```python
# Establish baseline before introducing variables
def establish_baseline(interface):
    """
    Test maximum achievable bandwidth under ideal conditions.
    This becomes the reference for all subsequent tests.
    """
    baseline_config = {
        'protocol': 'TCP',
        'streams': 1,
        'bandwidth': 'unlimited',  # Let TCP find maximum
        'duration': 30,
        'buffer_size': 'default',
    }
    
    # Run multiple iterations for statistical validity
    results = []
    for i in range(5):
        result = run_iperf_test(baseline_config)
        results.append(result['bandwidth'])
    
    baseline = {
        'mean': statistics.mean(results),
        'stdev': statistics.stdev(results),
        'min': min(results),
        'max': max(results),
    }
    
    return baseline
```

### Data Collection and Analysis

**Pattern: Continuous Monitoring with Periodic Sampling**

Snapshot diagnostics miss intermittent issues. Continuous collection with configurable sampling intervals captures transient failures.

**Implementation**:
```python
# Worker-based continuous collection
class DiagnosticScanner:
    def __init__(self, conn, interface, interval=5):
        self.conn = conn
        self.interface = interface
        self.interval = interval
        self.queue = queue.Queue()
        self.running = False
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def _collect_loop(self):
        while self.running:
            try:
                timestamp = datetime.now()
                stats = self._collect_stats()
                self.queue.put({
                    'timestamp': timestamp,
                    'stats': stats,
                })
            except Exception as e:
                logger.error(f"Collection failed: {e}")
                # Attempt reconnection
                self.conn = reconnect_with_backoff(self.conn)
            
            time.sleep(self.interval)
    
    def _collect_stats(self):
        return {
            'ethtool': parse_ethtool(self.conn.execute(f'ethtool -S {self.interface}')),
            'mlxlink': parse_mlxlink(self.conn.execute(f'mlxlink -d {self.interface}')),
        }
```

**CSV Export Pattern**:
```python
# Structured data export for post-analysis
def export_diagnostics_csv(data, output_dir):
    """
    Export collected data to CSV for trend analysis.
    Separate files for different metric types.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Interface statistics
    stats_df = pd.DataFrame([
        {
            'timestamp': d['timestamp'],
            'interface': d['interface'],
            'rx_bytes': d['stats']['rx_bytes'],
            'tx_bytes': d['stats']['tx_bytes'],
            'rx_errors': d['stats']['rx_errors'],
            'tx_errors': d['stats']['tx_errors'],
        }
        for d in data
    ])
    stats_df.to_csv(f'{output_dir}/{timestamp}_stats.csv', index=False)
    
    # Link diagnostics
    link_df = pd.DataFrame([
        {
            'timestamp': d['timestamp'],
            'interface': d['interface'],
            'link_state': d['mlxlink']['state'],
            'speed': d['mlxlink']['speed'],
            'ber': d['mlxlink']['ber'],
        }
        for d in data
    ])
    link_df.to_csv(f'{output_dir}/{timestamp}_link.csv', index=False)
```

### Error Handling and Recovery

**Pattern: Graceful Degradation with Automatic Reconnection**

Network diagnostics operate in unreliable environments. Connection failures should trigger automatic recovery without losing collected data.

**Implementation**:
```python
class ResilientConnection:
    def __init__(self, host, max_retries=3):
        self.host = host
        self.max_retries = max_retries
        self.conn = None
        self._connect()
    
    def _connect(self):
        for attempt in range(self.max_retries):
            try:
                self.conn = paramiko.SSHClient()
                self.conn.connect(self.host, timeout=30)
                logger.info(f"Connected to {self.host}")
                return
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def execute(self, cmd, timeout=30):
        """Execute command with automatic reconnection on failure."""
        for attempt in range(self.max_retries):
            try:
                stdin, stdout, stderr = self.conn.exec_command(cmd, timeout=timeout)
                exit_status = stdout.channel.recv_exit_status()
                output = stdout.read().decode()
                
                if exit_status != 0:
                    error = stderr.read().decode()
                    raise CommandError(f"Command failed: {error}")
                
                return output
            
            except (socket.timeout, paramiko.SSHException) as e:
                logger.warning(f"Execution failed (attempt {attempt+1}): {e}")
                if attempt < self.max_retries - 1:
                    self._connect()  # Reconnect and retry
                else:
                    raise
```

## Anti-Patterns to Avoid

### 1. Silent Timeout Failures

**Problem**: SSH connections timeout during long operations (eye scans, traffic tests) without keepalive, losing all collected data.

**Symptom**: "Broken pipe" or "Connection reset" errors after 5-10 minutes of operation.

**Solution**: Configure both client and server keepalive intervals. Use `ServerAliveInterval=60` on client and `ClientAliveInterval=120` on server.

### 2. Unidirectional Traffic Testing

**Problem**: Testing only client→server direction misses asymmetric routing issues, QoS policies, or hardware problems affecting the reverse path.

**Symptom**: Forward path achieves 10G but reverse path only 5G, discovered only after deployment.

**Solution**: Always run bidirectional tests with role reversal. Collect per-interface statistics for both directions.

### 3. Snapshot Diagnostics for Intermittent Issues

**Problem**: Single-point-in-time diagnostics miss transient failures that occur between samples.

**Symptom**: "Works fine when I check it" but users report intermittent failures.

**Solution**: Implement continuous monitoring with configurable sampling intervals (1-10 seconds). Export time-series data for trend analysis.

### 4. Testing Without Baseline

**Problem**: Running performance tests without establishing known-good baseline makes it impossible to determine if results are acceptable.

**Symptom**: "Is 8.5G throughput good?" without context of maximum achievable bandwidth.

**Solution**: Always establish baseline under ideal conditions first. Test with single stream, unlimited bandwidth, default settings. Use this as reference for all subsequent tests.

### 5. Ignoring Physical Layer

**Problem**: Jumping directly to higher-layer diagnostics (ping, traceroute) when physical layer issues exist.

**Symptom**: Spending hours debugging routing when cable is unplugged or has high BER.

**Solution**: Always start with physical layer verification: link state, speed, duplex, cable type, BER. Use `ethtool` and `mlxlink` before network-layer tools.

### 6. Hardcoded Timeouts

**Problem**: Using fixed timeouts for operations with variable duration (eye scans: 30-120s depending on configuration).

**Symptom**: Premature timeout failures on slower hardware or complex operations.

**Solution**: Make timeouts configurable based on operation type. Use generous defaults (2-3x expected duration) with user override capability.

### 7. No Error Context

**Problem**: Logging errors without context (which interface, which operation, what parameters).

**Symptom**: "Command failed" logs that provide no actionable information for debugging.

**Solution**: Include full context in error messages: timestamp, interface, command, parameters, exit code, stderr output.

### 8. Synchronous Blocking Operations

**Problem**: Running long operations (traffic tests, eye scans) synchronously in main thread, blocking UI and other operations.

**Symptom**: Unresponsive interface during data collection, inability to monitor multiple interfaces simultaneously.

**Solution**: Use worker threads with queue-based communication. Separate data collection from UI updates. Implement cancellation mechanisms.

### 9. Credential Hardcoding

**Problem**: Embedding passwords in configuration files or code.

**Symptom**: Security vulnerabilities, inability to share configurations, credential rotation difficulties.

**Solution**: Use Pydantic `SecretStr` for password fields. Load from environment variables or secure credential stores. Never log or display passwords.

### 10. Missing Reconnection Logic

**Problem**: Treating connection failures as fatal errors without retry attempts.

**Symptom**: Single network hiccup terminates entire diagnostic session, losing all progress.

**Solution**: Implement exponential backoff retry logic. Preserve collected data across reconnection attempts. Make retry count configurable.

## Implementation Guidelines

### Step 1: Connection Establishment

```python
# 1. Configure keepalive parameters
ssh_config = {
    'ServerAliveInterval': 60,
    'ServerAliveCountMax': 3,
    'ConnectTimeout': 30,
}

# 2. Establish connection with retry logic
conn = ResilientConnection(
    host='target.example.com',
    jump_hosts=['bastion.example.com'],
    config=ssh_config,
    max_retries=3,
)

# 3. Verify connectivity
conn.execute('echo "Connection test"')
```

### Step 2: Baseline Collection

```python
# 1. Identify target interfaces
interfaces = conn.execute('ip link show').parse_interfaces()

# 2. Collect physical layer baseline
for iface in interfaces:
    baseline = {
        'link_state': ethtool.get_link(conn, iface),
        'speed': ethtool.get_speed(conn, iface),
        'duplex': ethtool.get_duplex(conn, iface),
    }
    
    if baseline['link_state'] != 'up':
        logger.warning(f"{iface}: Link down, skipping")
        continue
    
    # 3. Establish traffic baseline
    traffic_baseline = establish_baseline(conn, iface)
    
    # 4. Store for comparison
    save_baseline(iface, baseline, traffic_baseline)
```

### Step 3: Continuous Monitoring

```python
# 1. Start scanner workers
scanners = []
for iface in interfaces:
    scanner = DiagnosticScanner(
        conn=conn,
        interface=iface,
        interval=5,  # 5-second sampling
    )
    scanner.start()
    scanners.append(scanner)

# 2. Collect data for specified duration
time.sleep(monitoring_duration)

# 3. Stop scanners and export data
for scanner in scanners:
    scanner.stop()
    data = scanner.get_collected_data()
    export_diagnostics_csv(data, output_dir)
```

### Step 4: Traffic Testing

```python
# 1. Run bidirectional baseline test
baseline_results = run_bidirectional_test({
    'forward': {'server': host_a, 'client': host_b, 'bandwidth': 'unlimited'},
    'reverse': {'server': host_b, 'client': host_a, 'bandwidth': 'unlimited'},
})

# 2. Run tests with varying parameters
test_matrix = [
    {'streams': 1, 'bandwidth': '10G'},
    {'streams': 4, 'bandwidth': '10G'},
    {'streams': 8, 'bandwidth': '10G'},
]

results = []
for params in test_matrix:
    result = run_bidirectional_test({
        'forward': {**baseline_config, **params},
        'reverse': {**baseline_config, **params},
    })
    results.append(result)

# 3. Compare against baseline
for result in results:
    deviation = calculate_deviation(result, baseline_results)
    if deviation > 10:  # >10% deviation
        logger.warning(f"Performance degradation detected: {deviation}%")
```

### Step 5: Analysis and Reporting

```python
# 1. Load collected data
stats_df = pd.read_csv(f'{output_dir}/stats.csv')
link_df = pd.read_csv(f'{output_dir}/link.csv')

# 2. Detect anomalies
anomalies = detect_anomalies(stats_df, threshold=3)  # 3 sigma

# 3. Generate report
report = {
    'summary': generate_summary(stats_df, link_df),
    'anomalies': anomalies,
    'recommendations': generate_recommendations(anomalies),
}

# 4. Export report
export_report(report, f'{output_dir}/analysis_report.json')
```

## Success Metrics

### Connection Reliability
- **Target**: >99% connection uptime during diagnostic sessions
- **Measurement**: `(total_time - disconnected_time) / total_time`
- **Threshold**: Alert if <95%

### Data Collection Completeness
- **Target**: >98% of scheduled samples collected successfully
- **Measurement**: `collected_samples / expected_samples`
- **Threshold**: Alert if <95%

### Diagnostic Accuracy
- **Target**: Root cause identified within 3 diagnostic layers
- **Measurement**: Average layers traversed before issue identification
- **Threshold**: Alert if >5 layers required

### Time to Diagnosis
- **Target**: <10 minutes for common issues (link down, high BER, routing)
- **Measurement**: Time from symptom report to root cause identification
- **Threshold**: Alert if >30 minutes

### Traffic Test Consistency
- **Target**: <5% variance between repeated baseline tests
- **Measurement**: `stdev(baseline_results) / mean(baseline_results)`
- **Threshold**: Alert if >10%

### Reconnection Success Rate
- **Target**: >95% of connection failures recovered automatically
- **Measurement**: `successful_reconnections / total_connection_failures`
- **Threshold**: Alert if <90%

## Sources & References

Content was rephrased for compliance with licensing restrictions.

References:
[1] Best Practices for Preventing SSH Timeout Problems - https://devops.aibit.im/article/best-practices-preventing-ssh-timeouts
[2] How to Keep SSH Session Alive - https://idroot.us/keep-ssh-session-alive/
[3] Configure Advanced SSH Client Settings for Optimal Performance and Security - https://devops.aibit.im/article/configure-advanced-ssh-client-settings
[4] SSH Timeouts Causes and Solutions for Developers - https://moldstud.com/articles/p-ssh-timeouts-common-causes-and-effective-solutions-for-developers
[5] Mastering Iperf3 for Comprehensive Network Testing - https://linuxhaxor.net/code/iperf3-commands.html
[6] Your Guide To Network Speed Testing - https://grandavehousing.calpoly.edu/news/mastering-iperf-your-guide-to
[7] IPerf testing considerations - https://www.kuncar.net/blog/2019/iperf-testing-considerations/
[8] Common Network Infrastructure Errors to Avoid - https://moldstud.com/articles/p-10-common-network-infrastructure-mistakes-and-how-to-avoid-them
[9] Network Troubleshooting Tales and Tips - https://www.networkdefenseblog.com/post/network-troubleshooting-tips
[10] How to Troubleshoot General Networking Issues - https://www.cbtnuggets.com/blog/technology/networking/how-to-troubleshoot-general-networking-issues
[11] Network monitoring of encrypted connections - https://www.ssh.com/academy/network/monitoring
[12] Check Active SSH Connections - https://zuzia.app/recipes/check-active-ssh-connections-linux/
[13] Link Diagnostic Per Port - https://docs.nvidia.com/networking/display/nvidiamlnxosusermanualv3114002/link+diagnostic+per+port

## Version History

- v1.0 (2026-01-15 15:14:27): Initial version based on research of SSH connection management, iperf testing, network troubleshooting, and interface diagnostics
