---
title:        Structure Foundation
inclusion:    always
version:      1.1
last-updated: 2026-01-15 16:20:00
status:       active
---

# Structure Foundation

## Directory Layout

```
interface-check/
├── src/
│   ├── app.py                 # Application entry, GUI initialization
│   ├── core/                  # Business logic
│   │   ├── connect/           # Connection management
│   │   │   ├── ssh.py         # SshConnection with multi-hop, keepalive
│   │   │   └── local.py       # LocalConnection wrapper
│   │   ├── scanner/           # Data collection workers
│   │   │   ├── slx.py         # SLX switch scanner
│   │   │   └── sut.py         # System Under Test scanner
│   │   ├── traffic/iperf/     # Iperf server, client, monitoring
│   │   ├── config/            # Configuration models
│   │   │   ├── scan.py        # ScanConfig
│   │   │   └── traffic.py     # TrafficConfig
│   │   ├── parser/            # Output parsers (SLX, SUT)
│   │   ├── log/               # Logging setup, rotation, formatting
│   │   ├── enum/              # LogMsg, LogName, ConnectType enums
│   │   ├── worker.py          # Worker thread management
│   │   ├── agent.py           # Agent coordination
│   │   ├── statistics.py      # Statistics collection
│   │   ├── analyze.py         # Log analysis
│   │   └── helpers.py         # Utility functions
│   ├── interfaces/            # Abstract interfaces
│   │   ├── component.py       # IConnection, ITool, IParser
│   │   ├── scanner.py         # IScanner
│   │   ├── configuration.py   # IConfiguration
│   │   └── ui.py              # ITab, IPanel
│   ├── models/                # Pydantic models
│   │   ├── config.py          # Host, Route, Settings, Config
│   │   └── scanner.py         # BaseScanner
│   ├── platform/              # Platform-specific
│   │   ├── tools/             # Network tools
│   │   │   ├── ethtool.py     # Interface statistics
│   │   │   ├── mlx.py         # Mellanox diagnostics (mlxlink, mlxconfig)
│   │   │   ├── mst.py         # MST integration
│   │   │   ├── rdma.py        # RDMA interface monitoring
│   │   │   ├── dmesg.py       # Kernel message parsing
│   │   │   ├── system.py      # System information
│   │   │   └── tool_factory.py # ToolFactory
│   │   ├── enums/             # ToolType, CmdInputType, SoftwareType
│   │   ├── hardware.py        # Hardware information collection
│   │   ├── health.py          # System health monitoring
│   │   ├── statistics.py      # Network statistics gathering
│   │   ├── power.py           # Power consumption monitoring
│   │   ├── platform.py        # Platform abstraction
│   │   └── software_manager.py # Package management (apt/yum)
│   └── ui/                    # Web UI
│       ├── gui.py             # Main GUI controller
│       ├── tabs/              # Tab implementations
│       │   ├── base.py        # BaseTab, BasePanel
│       │   ├── host.py        # SSH Host Manager
│       │   ├── local.py       # Local diagnostics
│       │   ├── slx.py         # SLX monitoring
│       │   ├── system.py      # System health
│       │   ├── agent.py       # Agent management
│       │   ├── chat.py        # Chat interface
│       │   ├── cable.py       # Cable diagnostics
│       │   ├── database.py    # Database management
│       │   ├── e2e.py         # End-to-end testing
│       │   ├── toolbox.py     # Tool collection
│       │   └── log.py         # Log viewer
│       ├── handlers/          # Business logic handlers
│       │   ├── host.py        # Host connection handling
│       │   ├── settings.py    # Settings management
│       │   └── graph.py       # Graph data processing
│       ├── components/        # Reusable UI components
│       │   ├── selector.py    # Generic selector
│       │   ├── host_selector.py # Host selection
│       │   └── dialogs.py     # Dialog components
│       ├── enums/             # UI enumerations
│       │   ├── gui.py         # GUI-related enums
│       │   ├── log_level.py   # Log level enums
│       │   └── settings.py    # Settings enums
│       └── themes/style.py    # LightTheme, apply_global_theme()
├── main.py                    # Interface monitoring entry
├── main_scan.py               # Interface scanning entry
├── main_scan_traffic.py       # Traffic testing entry
├── main_scan_analyze.py       # Log analysis entry
├── main_scan_cfg.json         # Scanning configuration
└── main_scan_traffic_cfg.json # Traffic configuration
```

## Key Components

### Connection Layer (`src/core/connect/`)
- **IConnection**: Abstract interface for connection types
- **SshConnection**: Multi-hop SSH with keepalive thread, context manager
- **LocalConnection**: Local command execution wrapper

### Tool Layer (`src/platform/tools/`)
- **ITool**: Abstract interface for diagnostic tools
- **Tool**: Base class with `_exec()`, `_results` dict
- **ToolFactory**: Creates tools by ToolType enum
- Tools: EthtoolTool, MlxTool, MstTool, RdmaTool, DmesgTool, SystemTool

### Scanner Layer (`src/core/scanner/`)
- **BaseScanner**: Abstract base for scanner implementations
- **SlxScanner**: SLX switch eye scan and DSC diagnostics
- **SutScanner**: System Under Test monitoring with configurable components

### UI Layer (`src/ui/`)
- **Gui**: Main controller, tab management, window lifecycle
- **BaseTab/BasePanel**: Abstract base classes for consistent structure
- **Handlers**: Separate business logic from UI (host, settings, graph)
- **Components**: Reusable UI elements (selectors, dialogs)
- **Themes**: Centralized styling with Tailwind classes

### Data Layer (`src/models/`)
- **Host**: IP, username, SecretStr password, info
- **Route**: Target host + jump hosts list
- **Config**: Root configuration combining Settings + Networks
- **BaseScanner**: Scanner configuration and state

### Platform Layer (`src/platform/`)
- **Hardware**: Hardware information collection
- **Health**: System health monitoring (temperature, sensors)
- **Statistics**: Network statistics gathering
- **Power**: Power consumption monitoring
- **SoftwareManager**: Package management (apt/yum)

## Key Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| IConnection interface | `interfaces/component.py` | Polymorphic connections |
| Factory | `platform/tools/tool_factory.py` | Tool creation by type |
| Context Manager | `core/connect/ssh.py` | Resource cleanup |
| Handler | `ui/handlers/` | Separate UI from logic |
| BaseTab/BasePanel | `ui/tabs/base.py` | Consistent UI structure |
| Worker Thread | `core/worker.py` | Background task execution |
| Scanner | `core/scanner/` | Data collection automation |

## Entry Points

| Script | Purpose | Key Classes |
|--------|---------|-------------|
| `main.py` | Web GUI | App, Gui |
| `main_scan.py` | Scanning | ScanConfig, SlxScanner, SutScanner |
| `main_scan_traffic.py` | Traffic | TrafficConfig, IperfServer, IperfClient |
| `main_scan_analyze.py` | Analysis | Analyzer |

## Version History

- v1.0 (2026-01-14 00:00:00): Initial structure foundation
- v1.1 (2026-01-15 16:20:00): Updated with complete directory structure, added missing components, expanded layer descriptions
