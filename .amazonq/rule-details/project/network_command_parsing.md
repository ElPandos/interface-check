# Network Command Output Parsing Guidelines

## Ethtool Output Parsing

### Standard Interface Information
```python
def parse_ethtool_interface(output: str) -> EthtoolInterface:
    """Parse ethtool interface information output."""
    lines = output.strip().split('\n')
    
    interface_data = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            interface_data[key.strip()] = value.strip()
    
    return EthtoolInterface(
        speed=interface_data.get('Speed'),
        duplex=interface_data.get('Duplex'),
        link_detected=interface_data.get('Link detected') == 'yes',
        auto_negotiation=interface_data.get('Auto-negotiation') == 'on'
    )
```

### Statistics Parsing
```python
def parse_ethtool_statistics(output: str) -> Dict[str, int]:
    """Parse ethtool -S output for interface statistics."""
    stats = {}
    lines = output.strip().split('\n')[1:]  # Skip header
    
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            try:
                stats[key.strip()] = int(value.strip())
            except ValueError:
                # Handle non-numeric values
                stats[key.strip()] = value.strip()
    
    return stats
```

## MLX Command Parsing

### MLXConfig Output
```python
@dataclass(frozen=True)
class MlxConfigParameter:
    name: str
    current_value: str
    default_value: str
    description: str

def parse_mlxconfig_query(output: str) -> List[MlxConfigParameter]:
    """Parse mlxconfig -d <device> query output."""
    parameters = []
    lines = output.strip().split('\n')
    
    for line in lines:
        if line.startswith('         '):  # Parameter line
            parts = line.strip().split()
            if len(parts) >= 3:
                parameters.append(MlxConfigParameter(
                    name=parts[0],
                    current_value=parts[1],
                    default_value=parts[2],
                    description=' '.join(parts[3:]) if len(parts) > 3 else ''
                ))
    
    return parameters
```

## Error Handling in Parsing

### Robust Parsing Patterns
```python
def safe_parse_numeric(value: str, default: int = 0) -> int:
    """Safely parse numeric values with fallback."""
    try:
        return int(value.replace(',', ''))  # Handle comma separators
    except (ValueError, AttributeError):
        return default

def parse_with_fallback(output: str, parser_func: Callable) -> Any:
    """Parse output with fallback error handling."""
    try:
        return parser_func(output)
    except Exception as e:
        logger.warning(f"Parsing failed: {e}")
        return None
```

## Regular Expression Patterns

### Common Network Patterns
```python
import re

# MAC address pattern
MAC_PATTERN = re.compile(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}')

# IP address pattern
IP_PATTERN = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')

# Speed pattern (e.g., "1000Mb/s", "10Gb/s")
SPEED_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(Mb|Gb)/s')

def extract_speed_value(speed_str: str) -> int | None:
    """Extract numeric speed value in Mbps."""
    match = SPEED_PATTERN.search(speed_str)
    if match:
        value, unit = match.groups()
        multiplier = 1000 if unit == 'Gb' else 1
        return int(float(value) * multiplier)
    return None
```