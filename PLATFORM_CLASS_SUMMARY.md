# Platform Class - System Under Test (SUT) Management

## Overview
The `Platform` class in `src/utils/system.py` provides a comprehensive, manufacturer-independent framework for managing and monitoring System Under Test (SUT) units with both hardware and software functionality.

## Key Features

### ✅ Hardware Management
- **Hardware Info Collection**: CPU, memory, network interfaces
- **Temperature Monitoring**: CPU, GPU, ambient sensors
- **Power Management**: Battery status, AC adapter, power control
- **Interface Control**: Enable/disable network interfaces

### ✅ Software Management
- **Software Detection**: Check if software is installed
- **Version Checking**: Get software version information
- **Auto Installation**: Install missing software using package managers
- **Package Listing**: List all installed software

### ✅ Network Management
- **Interface Status**: Monitor all network interfaces
- **Connectivity Testing**: Test network connectivity
- **Interface Control**: Power up/down network interfaces

### ✅ Health Monitoring
- **System Metrics**: CPU, memory, disk usage
- **Temperature Logging**: Continuous temperature monitoring
- **Health History**: Track metrics over time
- **System Test Logging**: Log test results with timestamps

### ✅ Extensibility
- **Custom Probes**: Add custom system probes
- **Probe System**: Run individual or all probes
- **Manufacturer Independent**: Works with any system
- **Flexible Architecture**: Easy to extend for new SUT types

## Usage Examples

### Basic Platform Setup
```python
from src.utils.system import Platform

# Create platform instance
platform = Platform(connection, "SUT-001")

# Get hardware information
hw_info = platform.get_hardware_info()
print(f"CPU: {hw_info['cpu']}")
print(f"Interfaces: {hw_info['interfaces']}")
```

### Temperature Monitoring
```python
# Monitor different sensors
cpu_temp = platform.get_temperature("cpu")
gpu_temp = platform.get_temperature("gpu")
ambient_temp = platform.get_temperature("ambient")

print(f"CPU: {cpu_temp}°C, GPU: {gpu_temp}°C")
```

### Software Management
```python
# Check if software is installed
ethtool_info = platform.check_software("ethtool")
if not ethtool_info.installed:
    # Auto-install using appropriate package manager
    platform.install_software("ethtool")

# Get all installed software
software_list = platform.get_software_list()
```

### Network Management
```python
# Check network status
network_status = platform.get_network_status()
print(f"Interface status: {network_status}")

# Test connectivity
if platform.test_connectivity("8.8.8.8"):
    print("Internet connectivity OK")

# Control interface power
platform.control_interface_power("eth0", enable=True)
```

### Health Monitoring
```python
# Collect comprehensive health metrics
health = platform.collect_health_metrics()
print(f"CPU: {health.cpu_usage}%, Memory: {health.memory_usage}%")
print(f"Temperature: {health.temperature}°C")

# Get health history
history = platform.get_health_history(hours=24)
print(f"Collected {len(history)} health samples")
```

### Custom Probes
```python
from src.utils.system import SystemProbe

class CustomProbe(SystemProbe):
    def probe(self):
        return {"custom_metric": 42, "status": "healthy"}

# Add custom probe
platform.add_probe("custom_health", CustomProbe())

# Run all probes
results = platform.run_all_probes()
print(f"Probe results: {results}")
```

### System Testing
```python
# Log system test results
connectivity_ok = platform.test_connectivity()
platform.log_system_test("connectivity_test", connectivity_ok, "Ping to 8.8.8.8")

temp = platform.get_temperature()
platform.log_system_test("temperature_test", temp < 80, f"CPU temp: {temp}°C")
```

## Data Structures

### SystemHealth
```python
@dataclass
class SystemHealth:
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    temperature: float = 0.0
    network_status: Dict[str, bool] = field(default_factory=dict)
    power_status: str = "unknown"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
```

### SoftwareInfo
```python
@dataclass
class SoftwareInfo:
    name: str
    version: str = "unknown"
    installed: bool = False
    path: Optional[str] = None
```

## Manufacturer Independence

The Platform class is designed to be manufacturer-independent:

- **Generic Commands**: Uses standard Linux commands that work across distributions
- **Auto-Detection**: Automatically detects package managers (apt, yum, dnf, pacman, zypper)
- **Flexible Sensors**: Supports various temperature sensor types
- **Standard Interfaces**: Uses `/sys/class/net` for network interface discovery
- **Extensible Probes**: Custom probes can be added for manufacturer-specific features

## Multi-SUT Support

The Platform class is designed for managing multiple SUT units:

- **Named Instances**: Each platform has a unique name identifier
- **Independent State**: Each instance maintains its own state and cache
- **Concurrent Safe**: Can be used with multiple connections simultaneously
- **Scalable**: Lightweight design suitable for managing many SUT units

## Integration with Existing Code

The Platform class integrates seamlessly with the existing codebase:

- **Connection Interface**: Works with any connection type (SSH, local, etc.)
- **Logging Integration**: Uses the existing logging framework
- **Error Handling**: Follows established error handling patterns
- **Type Safety**: Full type hints for better IDE support

## Benefits

1. **Comprehensive**: Covers hardware, software, network, and health monitoring
2. **Flexible**: Extensible probe system for custom requirements
3. **Independent**: Manufacturer-independent design
4. **Scalable**: Suitable for managing multiple SUT units
5. **Integrated**: Works with existing connection and logging systems
6. **Type Safe**: Full type annotations for better development experience
7. **Testable**: Easy to mock and test individual components

The Platform class provides a solid foundation for comprehensive SUT management that can be easily extended and customized for specific testing requirements while remaining manufacturer-independent and highly reusable.