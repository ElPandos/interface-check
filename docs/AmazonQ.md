# Interface Check - Amazon Q Developer Configuration

## Project Overview

Interface Check is a network interface monitoring and diagnostic tool that provides a web-based GUI for managing and analyzing network interfaces on remote systems via SSH connections.

### Architecture
- **Frontend**: NiceGUI-based web interface with tabbed navigation
- **Backend**: Python 3.13+ with SSH-based remote command execution
- **Communication**: SSH tunneling through jump hosts to target systems
- **Data Processing**: Real-time network interface analysis and visualization

### Key Technologies
- **NiceGUI 2.24.2**: Modern web UI framework
- **Paramiko 4.0.0+**: SSH client library
- **Plotly 6.3.1+**: Interactive data visualization
- **Pandas 2.3.3+**: Data manipulation
- **Pydantic**: Configuration and data validation

## Primary Workflows

### Development
1. **Environment Setup**: `uv sync` → `source .venv/bin/activate`
2. **Code Quality**: `uv run ruff check . --fix` → `uv run mypy .`
3. **Testing**: `uv run pytest` with coverage reporting
4. **Running**: `uv run main.py` for development mode

### Network Diagnostics
1. **Connection**: SSH tunnel through jump host to target
2. **Interface Discovery**: Enumerate network interfaces
3. **Tool Execution**: ethtool, mlxconfig, mlxlink, ipmitool
4. **Data Visualization**: Real-time graphs and metrics

## Code Standards

### Type Safety
- **Comprehensive type hints** on all functions and methods
- **Union types** for multiple possibilities: `str | None`
- **Generic collections**: `List[str]`, `Dict[str, Any]`
- **Dataclasses** with `frozen=True` for immutable data

### Documentation
- **Google-style docstrings** for all public APIs
- **Inline comments** for complex logic
- **Error context** in exception handling

### Architecture Patterns
- **Tab-Panel separation**: UI tabs separate from content panels
- **Handler pattern**: Business logic separated from UI
- **SSH connection sharing**: Centralized connection management
- **Configuration-driven**: JSON-based settings

## File Structure

```
src/
├── app.py              # Main application entry
├── ui/
│   ├── gui.py          # Primary GUI controller
│   ├── tabs/           # Tab implementations
│   ├── handlers/       # Business logic handlers
│   └── components/     # Reusable UI components
├── utils/
│   ├── route.py  # SSH management
│   ├── commands.py        # Command execution
│   └── system.py          # System operations
└── models/
    └── configurations.py  # Data models
```

## Development Guidelines

When working with this codebase:
- Follow the established tab-panel architecture pattern
- Use the shared SSH connection instance across components
- Implement proper error handling with logging
- Add comprehensive type hints and docstrings
- Test SSH operations with proper connection lifecycle management
- Use NiceGUI's reactive patterns for UI updates
