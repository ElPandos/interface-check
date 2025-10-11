# SSH Operations and Network Commands

## SSH Connection Lifecycle
```python
# Proper connection usage
if not ssh_connection.is_connected():
    if not ssh_connection.connect():
        logger.error("Failed to establish SSH connection")
        return

try:
    stdout, stderr = ssh_connection.exec_command("ethtool eth0")
    if stderr:
        logger.warning(f"Command stderr: {stderr}")
    return parse_output(stdout)
except Exception as e:
    logger.exception("Command execution failed")
    return None
```

## Command Execution Patterns
- **Timeout handling**: Always specify reasonable timeouts
- **Error checking**: Check both stderr and return codes
- **Output parsing**: Use dedicated parser classes
- **Logging**: Log command execution for debugging

## Network Tool Integration
- **ethtool**: Interface statistics and configuration
- **mlxconfig**: Mellanox adapter configuration
- **mlxlink**: Mellanox link diagnostics
- **ipmitool**: IPMI management interface

## Data Processing
```python
@dataclass(frozen=True)
class NetworkInterface:
    name: str
    speed: str | None
    duplex: str | None
    link_detected: bool

def parse_ethtool_output(output: str) -> NetworkInterface:
    # Parse command output into structured data
    pass
```

## Error Recovery
- **Connection failures**: Automatic reconnection with backoff
- **Command timeouts**: Graceful handling with user notification
- **Partial failures**: Continue operation with available data
- **Resource cleanup**: Proper connection disposal
