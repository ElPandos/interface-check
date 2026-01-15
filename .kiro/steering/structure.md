---
title:        Structure Foundation
inclusion:    always
version:      1.0
last-updated: 2026-01-14 12:48:00
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
│   │   ├── config/            # Dataclass configurations
│   │   │   ├── scan.py        # ScanConfig
│   │   │   └── traffic.py     # TrafficConfig
│   │   ├── parser/            # Output parsers (SLX, SUT)
│   │   ├── log/               # Logging setup, rotation, formatting
│   │   └── enum/              # LogMsg, LogName enums
│   ├── interfaces/            # Abstract interfaces
│   │   └── component.py       # IConnection, ITool, IParser
│   ├── models/                # Pydantic models
│   │   └── config.py          # Host, Route, Settings, Config
│   ├── platform/              # Platform-specific
│   │   ├── tools/             # Network tools
│   │   │   ├── ethtool.py     # Interface statistics
│   │   │   ├── mlx.py         # Mellanox diagnostics
│   │   │   ├── mst.py         # MST integration
│   │   │   └── tool_factory.py # ToolFactory
│   │   └── enums/             # ToolType, CmdInputType
│   └── ui/                    # Web UI
│       ├── gui.py             # Main GUI controller
│       ├── tabs/              # Tab implementations
│       │   ├── base.py        # BaseTab, BasePanel
│       │   ├── host.py        # SSH Host Manager
│       │   ├── local.py       # Local diagnostics
│       │   └── slx.py         # SLX monitoring
│       ├── handlers/          # Business logic handlers
│       ├── components/        # Reusable UI components
│       └── themes/style.py    # LightTheme, apply_global_theme()
├── main.py                    # Interface monitoring entry
├─�� main_scan.py               # Interface scanning entry
├── main_scan_traffic.py       # Traffic testing entry
└── main_scan_analyze.py       # Log analysis entry
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
- Tools: EthtoolTool, MlxTool, MstTool, RdmaTool, SystemTool

### UI Layer (`src/ui/`)
- **Gui**: Main controller, tab management
- **BaseTab/BasePanel**: Abstract base classes
- **Handlers**: Separate business logic from UI
- **Themes**: Centralized styling with Tailwind classes

### Data Layer (`src/models/`)
- **Host**: IP, username, SecretStr password
- **Route**: Target host + jump hosts list
- **Config**: Root configuration combining Settings + Networks

## Key Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| IConnection interface | `interfaces/component.py` | Polymorphic connections |
| Factory | `platform/tools/tool_factory.py` | Tool creation by type |
| Context Manager | `core/connect/ssh.py` | Resource cleanup |
| Handler | `ui/handlers/` | Separate UI from logic |
| BaseTab/BasePanel | `ui/tabs/base.py` | Consistent UI structure |

## Entry Points

| Script | Purpose | Key Classes |
|--------|---------|-------------|
| `main.py` | Web GUI | App, Gui |
| `main_scan.py` | Scanning | ScanConfig, SlxScanner, SutScanner |
| `main_scan_traffic.py` | Traffic | TrafficConfig, IperfServer, IperfClient |
| `main_scan_analyze.py` | Analysis | Analyzer |

## Version History

- v1.0 (2026-01-14 00:00:00): Initial structure foundation
