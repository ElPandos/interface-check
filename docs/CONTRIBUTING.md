# Contributing to Interface Check

Thank you for your interest in contributing! This document provides guidelines and best practices for development.

## Development Setup

### Prerequisites
- Python 3.13+
- `uv` package manager
- Git

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd interface-check

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Install pre-commit hooks
pre-commit install
```

## Code Standards

### Type Hints
All functions and methods must include complete type annotations:

```python
def process_data(input: str, timeout: int = 30) -> dict[str, Any]:
    """Process input data with timeout."""
    ...
```

### Documentation
Use Google-style docstrings for all public classes and methods:

```python
def connect(self, host: str, port: int = 22) -> bool:
    """Establish SSH connection to host.
    
    Args:
        host: Target hostname or IP address
        port: SSH port number (default: 22)
        
    Returns:
        True if connection successful, False otherwise
        
    Raises:
        ConnectionError: If connection fails after retries
    """
    ...
```

### Error Handling
Always use comprehensive error handling with logging:

```python
try:
    result = risky_operation()
    return result
except SpecificError as e:
    logger.exception("Operation failed: %s", e)
    return default_value
```

### Logging
Use appropriate log levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for recoverable issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

```python
logger.debug("Processing item %d of %d", i, total)
logger.info("Connection established to %s", host)
logger.warning("Retry attempt %d/%d", attempt, max_attempts)
logger.error("Failed to parse output: %s", output[:100])
```

## Code Quality Tools

### Formatting
```bash
# Format code with Ruff (recommended)
uv run ruff format .

# Check formatting without changes
uv run ruff format . --check
```

### Linting
```bash
# Run Ruff linter
uv run ruff check .

# Auto-fix issues
uv run ruff check . --fix
```

### Type Checking
```bash
# Run MyPy type checker
uv run mypy .
```

### Testing
```bash
# Run tests with coverage
uv run pytest --cov=src

# Run specific test file
uv run pytest tests/test_example.py

# Run with minimal output
uv run pytest -q
```

## Project Structure

```
interface-check/
├── src/
│   ├── app.py            # Main application entry point
│   ├── core/             # Core functionality
│   │   ├── connect/      # SSH connection management
│   │   ├── traffic/      # Traffic testing (iperf)
│   │   ├── scanner/      # SLX and SUT scanners
│   │   ├── config/       # Configuration models
│   │   ├── parser/       # Output parsers
│   │   └── log/          # Logging setup
│   ├── interfaces/       # Abstract interfaces
│   ├── models/           # Data models (Pydantic)
│   ├── platform/         # Platform-specific tools
│   │   ├── tools/        # Network diagnostic tools
│   │   └── enums/        # Platform enumerations
│   └── ui/               # User interface (NiceGUI)
│       ├── tabs/         # Individual tab implementations
│       ├── handlers/     # Business logic handlers
│       ├── components/   # Reusable UI components
│       └── themes/       # UI styling
├── tests/                # Test files
├── logs/                 # Application logs and CSV outputs
├── main.py               # Interface monitoring tool
├── main_scan.py          # Interface scanning tool
├── main_scan_analyze.py  # Log analysis tool
└── main_scan_traffic.py  # Traffic testing tool
```

## Common Patterns

### NiceGUI UI Development
```python
# Tab implementation pattern
from src.ui.tabs.base import BaseTab
from nicegui import ui

class CustomTab(BaseTab):
    def __init__(self, gui_handler):
        super().__init__(gui_handler)
        self.title = "Custom Tab"
    
    def create_content(self):
        with ui.column().classes('w-full gap-4'):
            ui.label('Custom Tab Content')
            self.create_controls()
    
    def create_controls(self):
        with ui.row().classes('gap-2'):
            ui.button('Action', on_click=self.handle_action)
    
    def handle_action(self):
        # Handle button click
        pass
```

### Configuration Handling
```python
# Load configuration with validation
from src.models.config import ScanConfig
from pydantic import ValidationError

try:
    config = ScanConfig.from_file('main_scan_cfg.json')
    logger.info("Configuration loaded successfully")
except ValidationError as e:
    logger.error("Configuration validation failed: %s", e)
    raise
```

### Traffic Testing Pattern
```python
# Iperf server management
from src.core.traffic.iperf import IperfServer

server = IperfServer(host='10.1.1.1', port=5001)
try:
    server.start()
    # Run tests
    client_results = run_iperf_clients()
finally:
    server.stop()
```

### SSH Connection Usage
```python
# Using SSH connection from core
from src.core.connect.ssh import SshConnection

# Context manager (recommended)
with SshConnection(host, user, password) as conn:
    result = conn.exec_cmd("ls -la")
    
# Manual management
conn = SshConnection(host, user, password)
if conn.connect():
    result = conn.exec_cmd("ls -la")
    conn.disconnect()
```

### Worker Thread Pattern
```python
# Background data collection
from src.core.scanner.sut import SutScanner
import threading

# Create and start scanner
scanner = SutScanner(config, ssh_connection)
scanner_thread = threading.Thread(target=scanner.run, daemon=True)
scanner_thread.start()

# Stop scanner
scanner.stop()
scanner_thread.join(timeout=5)
```

### Parser Implementation
```python
from src.interfaces.component import IParser

class CustomParser(IParser):
    """Parse custom command output."""
    
    def __init__(self, raw_data: str):
        super().__init__()
        self._raw_data = raw_data
        self._result = None
        self._parse()
    
    def name(self) -> str:
        return "custom_parser"
    
    def _parse(self) -> None:
        """Parse raw output into structured data."""
        # Implementation here
        lines = self._raw_data.strip().split('\n')
        self._result = {'lines': len(lines)}
        
    def get_result(self) -> dict:
        """Return parsed result."""
        return self._result
```

## Git Workflow

### Branch Naming
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
Follow conventional commits format:

```
type(scope): brief description

Detailed explanation if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Process
1. Create feature branch from `main`
2. Make changes with clear commits
3. Run all quality checks
4. Update documentation if needed
5. Submit PR with description
6. Address review comments
7. Squash and merge when approved

## Testing Guidelines

### Unit Tests
Test individual components in isolation:

```python
def test_parser_extracts_data():
    output = "Temperature: 45.5 C\nStatus: OK"
    parser = CustomParser(output)
    result = parser.get_result()
    assert result['lines'] == 2
```

### Integration Tests
Test component interactions:

```python
from unittest.mock import Mock

def test_scanner_collects_data():
    mock_ssh = Mock()
    mock_ssh.exec_cmd.return_value = "test output"
    
    scanner = SutScanner(config, mock_ssh)
    # Test scanner functionality
```

### Mocking
Use mocks for external dependencies:

```python
from unittest.mock import Mock, patch

@patch('src.core.connect.ssh.paramiko.SSHClient')
def test_ssh_connection(mock_client):
    conn = SshConnection("host", "user", "pass")
    assert conn.connect()
```

## Performance Considerations

### Memory Management
- Use `__slots__` for frequently instantiated classes
- Clear large data structures when no longer needed
- Use generators for large datasets

### Threading
- Use daemon threads for background tasks
- Implement proper shutdown mechanisms
- Use thread-safe queues for communication

### SSH Connections
- Reuse connections when possible
- Implement connection pooling for high-frequency operations
- Set appropriate timeouts

## Documentation

### Code Comments
- Explain **why**, not **what**
- Document complex algorithms
- Add TODO comments for future improvements

### Module Docstrings
Every module should have a docstring explaining its purpose:

```python
"""SSH connection management with multi-hop support.

This module provides SSH connection functionality including:
- Direct and multi-hop connections
- Automatic keepalive
- Interactive shell sessions
- Command execution with timeout
"""
```

### README Updates
Update README.md when adding:
- New features
- Configuration options
- Dependencies
- Usage examples

## Development Guidelines

For detailed development patterns and best practices, see the steering documentation:

- **[Development Guidelines](.kiro/steering/guidelines.md)** - Overview of all patterns
- **[Code Quality Standards](.kiro/steering/code-quality-standards.md)** - Type hints, documentation, error handling
- **[Architecture Patterns](.kiro/steering/architecture-patterns.md)** - Class design, threading, configuration
- **[UI Development Patterns](.kiro/steering/ui-development-patterns.md)** - NiceGUI patterns and user experience
- **[SSH Connection Patterns](.kiro/steering/ssh-connection-patterns.md)** - Connection management and security
- **[Threading Patterns](.kiro/steering/threading-patterns.md)** - Worker threads and synchronization

For contribution guidelines, see this document.

## Questions?

If you have questions or need clarification:
1. Check existing documentation in `.kiro/steering/`
2. Review similar code in the project
3. Ask in pull request comments
4. Contact maintainers

Thank you for contributing!
