# Config Extraction to src/core/config/

## Overview
Extracted configuration classes from main files to dedicated config modules for better organization and reusability.

## New Structure

```
src/core/config/
├── __init__.py          # Shared loading utilities
├── scan.py              # ScanConfig for main_scan.py
└── traffic.py           # TrafficConfig for main_scan_traffic.py
```

## Changes Made

### 1. Created Config Modules

**src/core/config/__init__.py:**
- `load_config_file()` - Generic config loader with PyInstaller support
- `load_scan_config()` - Loads main_scan_cfg.json → ScanConfig
- `load_traffic_config()` - Loads main_scan_traffic_cfg.json → TrafficConfig

**src/core/config/scan.py:**
- `ScanConfig` dataclass with all SLX/SUT settings
- `from_dict()` classmethod for JSON parsing

**src/core/config/traffic.py:**
- `TrafficConfig` dataclass with all iperf test settings
- `from_dict()` classmethod for JSON parsing

### 2. Updated Main Files

**main_scan.py:**
- Removed 100+ lines of Config class definition
- Removed `load_cfg()` function
- Import: `from src.core.config import load_scan_config`
- Usage: `cfg = load_scan_config(logger)`

**main_scan_traffic.py:**
- Removed 80+ lines of Config class definition
- Removed `load_cfg()` function
- Import: `from src.core.config import load_traffic_config`
- Usage: `cfg = load_traffic_config(logger)`

## Benefits

### Code Organization
- **Single Responsibility**: Each config module serves one purpose
- **Discoverability**: All configs in `src/core/config/`
- **Testability**: Config classes can be unit tested independently

### Reusability
- **Shared Loading Logic**: One `load_config_file()` for all configs
- **PyInstaller Support**: Centralized bundled executable handling
- **Type Safety**: Strong typing with dataclasses

### Maintainability
- **Reduced Duplication**: No duplicate loading logic
- **Cleaner Main Files**: 100+ lines removed from each main file
- **Isolated Changes**: Config changes don't affect main files

## Migration Summary

| File | Lines Removed | Lines Added | Net Change |
|------|---------------|-------------|------------|
| main_scan.py | ~110 | ~2 | -108 |
| main_scan_traffic.py | ~90 | ~2 | -88 |
| src/core/config/__init__.py | 0 | ~50 | +50 |
| src/core/config/scan.py | 0 | ~100 | +100 |
| src/core/config/traffic.py | 0 | ~80 | +80 |
| **Total** | ~200 | ~234 | +34 |

Net increase of 34 lines, but with significantly better organization.

## Usage Examples

### Loading Scan Config
```python
from src.core.config import load_scan_config

cfg = load_scan_config(logger)
print(cfg.slx_host, cfg.sut_host)
```

### Loading Traffic Config
```python
from src.core.config import load_traffic_config

cfg = load_traffic_config(logger)
print(cfg.server_host, cfg.client_host)
```

### Custom Config Loading
```python
from src.core.config import load_config_file
from src.core.config.scan import ScanConfig

cfg = load_config_file("custom_cfg.json", ScanConfig, logger)
```

## Testing Checklist
- [x] Syntax validation passed
- [ ] main_scan.py runs correctly
- [ ] main_scan_traffic.py runs correctly
- [ ] PyInstaller builds work
- [ ] Config validation still works
- [ ] Error messages are clear
