# Testing Strategy

## Test Structure
- **Unit tests**: Individual component testing in `tests/`
- **Integration tests**: SSH connection and command execution
- **UI tests**: NiceGUI component behavior
- **Mock objects**: Use for SSH connections in unit tests

## Testing Patterns
```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_ssh_connection():
    mock = Mock()
    mock.is_connected.return_value = True
    mock.exec_command.return_value = ("output", "")
    return mock

def test_command_execution(mock_ssh_connection):
    handler = CommandHandler(mock_ssh_connection)
    result = handler.execute_ethtool("eth0")
    assert result is not None
    mock_ssh_connection.exec_command.assert_called_once()
```

## Test Categories
- **SSH operations**: Mock paramiko for connection testing
- **Data parsing**: Test output parsers with known inputs
- **UI components**: Test component creation and event handling
- **Configuration**: Test config loading and validation

## Coverage Requirements
- **Minimum 80%** code coverage for core functionality
- **100%** coverage for critical paths (SSH, parsing)
- **Exception paths** must be tested
- **Edge cases** documented and tested

## Test Execution
- **Local**: `uv run pytest --cov=src`
- **CI/CD**: Automated testing in GitHub Actions
- **Performance**: Benchmark critical operations
- **Integration**: Test with real SSH connections in staging