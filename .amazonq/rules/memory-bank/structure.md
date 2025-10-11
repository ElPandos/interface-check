# Interface Check - Project Structure

## Directory Organization

### Core Application (`src/`)
- **`app.py`**: Main application entry point and lifecycle management
- **`ui/`**: User interface components and handlers
  - **`gui.py`**: Primary GUI controller and window management
  - **`tabs/`**: Individual tab implementations (host, ethtool, mlxconfig, etc.)
  - **`handlers/`**: Business logic for UI interactions
  - **`components/`**: Reusable UI components like connection selectors
  - **`enums/`**: UI-specific enumerations and constants

### Business Logic (`src/`)
- **`utils/`**: Core utilities and system interactions
  - **`ssh_connection.py`**: SSH connection management
  - **`system.py`**: System-level operations and logging
  - **`collector.py`**: Data collection and processing
  - **`commands.py`**: Command execution and parsing
  - **`interface.py`**: Network interface operations
- **`models/`**: Data models and structures
- **`enums/`**: Application-wide enumerations

### Configuration & Assets
- **`config/`**: Application configuration files (JSON-based)
- **`assets/`**: Static resources (icons, images)
- **`scripts/`**: Utility and deployment scripts

### Development & Testing
- **`tests/`**: Test suite and test utilities
- **`main*.py`**: Multiple entry points for different execution modes
- **`.devcontainer/`**: Development container configuration

## Architectural Patterns

### Layered Architecture
- **Presentation Layer**: NiceGUI-based web interface
- **Business Logic Layer**: Handlers and utilities for core functionality
- **Data Access Layer**: SSH connections and remote command execution

### Component Structure
- **Tab-based UI**: Modular interface with specialized tabs for different tools
- **Handler Pattern**: Separation of UI logic from business logic
- **Connection Management**: Centralized SSH connection handling with status tracking
- **Configuration-driven**: JSON-based configuration for flexibility

### Key Relationships
- `App` → `Gui` → `Tabs` → `Handlers` → `Utils`
- SSH connections shared across components via dependency injection
- Event-driven updates for connection status and data refresh