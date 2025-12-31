# Network Agent

The Network Agent is an intelligent automation system for network interface diagnostics and monitoring, implemented as part of the Interface Check web UI. It provides automated task execution and network analysis through the Agent tab.

## Features

### 🤖 Intelligent Automation
- **Automated Task Execution**: Run network diagnostic tasks through the web interface
- **Multi-screen Support**: Organize tasks across multiple screens in the UI
- **Real-time Execution**: Non-blocking task execution with live updates
- **SSH Integration**: Uses shared SSH connections for remote execution

### 🔧 Available Through Agent Tab

The Network Agent is accessible through the **Agent** tab in the web interface and provides:

- **Task Queue Management**: Organize and monitor diagnostic tasks
- **Real-time Status**: Track task execution progress
- **Results Display**: View detailed command outputs and analysis
- **Multi-screen Layout**: Support for multiple agent screens

### 📋 Task Management

- **Async Execution**: Non-blocking task execution
- **Connection Reuse**: Efficient SSH connection management
- **Error Handling**: Graceful handling of connection and command failures
- **Progress Tracking**: Real-time task status updates

## Usage

### Accessing the Agent

1. Start the Interface Check application (`uv run main.py`)
2. Navigate to the **Agent** tab in the web interface
3. Ensure SSH connection is established to target hosts
4. Use the agent interface to execute diagnostic tasks

### Integration

The Network Agent integrates with:

- **SSH Connection Management**: Uses `src/core/connect/` for remote execution
- **Multi-screen System**: Implemented in `src/core/screen.py`
- **Web UI Framework**: Built with NiceGUI in `src/ui/tabs/agent.py`
- **Configuration System**: Respects application configuration settings

## Technical Implementation

### Architecture
- **Agent Class**: Core automation engine (`src/core/agent.py`)
- **AgentTab**: NiceGUI tab implementation (`src/ui/tabs/agent.py`)
- **AgentPanel**: UI panel component with multi-screen support
- **BasePanel**: Inherits from base panel functionality

### Key Components
```python
# Core agent functionality
src/core/agent.py          # Agent automation engine
src/core/screen.py         # Multi-screen support

# UI implementation  
src/ui/tabs/agent.py       # Agent tab and panel
src/ui/tabs/base.py        # Base tab functionality
```

### Error Handling
- **Connection Failures**: Graceful handling of SSH connection issues
- **Command Timeouts**: Configurable timeout management
- **Partial Failures**: Continue operation with available data
- **User Feedback**: Clear error messages in the web interface

## Development

The Network Agent is part of the main Interface Check application. For development:

1. See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup
2. Agent-specific code is in `src/core/agent.py` and `src/ui/tabs/agent.py`
3. Follow the UI development patterns in `.kiro/steering/ui-development-patterns.md`
4. Test through the web interface at `http://localhost:8080`

## Future Enhancements

- **Enhanced Task Library**: More predefined diagnostic tasks
- **Intelligent Analysis**: AI-powered analysis of command outputs
- **Scheduled Tasks**: Cron-like scheduling for regular diagnostics
- **Report Generation**: Automated diagnostic reports
- **Integration APIs**: Connect with external monitoring systems
