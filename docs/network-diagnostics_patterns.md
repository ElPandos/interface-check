---
title:        Network Diagnostics Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# Network Diagnostics Patterns

## Purpose
Define patterns for network diagnostic tool integration in the interface-check project, including tool abstraction, command execution, and result handling.

## Core Patterns

### 1. Tool Interface Pattern
Abstract interface for diagnostic tools:

```python
class ITool(ABC):
    @property
    @abstractmethod
    def type(self) -> ToolType:
        """Get tool type identifier."""

    @abstractmethod
    def _parse(self, cmd: str, output: str) -> dict[str, str]:
        """Parse command output into structured data."""
```

**Benefits**: Consistent API across all network tools (ethtool, mlxlink, mst, etc.).

### 2. Tool Base Class Pattern
Common functionality for all tools:

```python
class Tool:
    def __init__(self, ssh: SshConnection, logger: logging.Logger | None = None):
        self._ssh = ssh
        self._results: dict[str, CmdResult] = {}
        self._logger = logger or logging.getLogger(LogName.MAIN.value)

    def _exec(self, cmd: str, timeout: int | None = 20) -> CmdResult:
        """Execute command and return result."""
        if not self._ssh.is_connected():
            return self._ssh.get_cr_msg_connection(cmd, LogMsg.EXEC_CMD_FAIL)
        
        cmd_result = self._ssh.exec_cmd(cmd, timeout=timeout)
        self._results[cmd] = cmd_result
        return cmd_result
```

### 3. Factory Pattern
Centralized tool creation:

```python
class ToolFactory:
    _TOOLS: ClassVar[dict[ToolType, type[ITool]]] = {
        ToolType.ETHTOOL: EthtoolTool,
        ToolType.MLX: MlxTool,
        ToolType.MST: MstTool,
        ToolType.RDMA: RdmaTool,
        ToolType.SYSTEM: SystemTool,
        ToolType.DMESG: DmesgTool,
    }

    @classmethod
    def create_tool(cls, tool_type: ToolType, ssh: SshConnection, interfaces: list[str]) -> ITool:
        if tool_type not in cls._TOOLS:
            raise ValueError(f"Unknown tool '{tool_type}'")
        return cls._TOOLS[tool_type](ssh, interfaces)
```

### 4. Command Template Pattern
Generate commands from templates with interface substitution:

```python
class EthtoolTool(Tool, ITool):
    _AVAILABLE_COMMANDS: ClassVar[list[list[Any]]] = [
        ["ethtool", CmdInputType.INTERFACE],
        ["ethtool", "-i", CmdInputType.INTERFACE],
        ["ethtool", "-S", CmdInputType.INTERFACE],
        ["ethtool", "-m", CmdInputType.INTERFACE],
    ]

    def _gen_cmds(self, interface: str, cmd: list[Any]) -> str:
        cmd_mod = []
        for part in cmd:
            match part:
                case CmdInputType.INTERFACE:
                    cmd_mod.append(interface)
                case CmdInputType.MST_PCICONF:
                    cmd_mod.append(helper.get_mst_device(self._ssh, interface))
                case _:
                    cmd_mod.append(part)
        return " ".join(cmd_mod)
```

### 5. Result Dataclass Pattern
Structured command results:

```python
@dataclass
class CmdResult:
    cmd: str
    stdout: str
    stderr: str
    exec_time: float
    rcode: int
    send_ms: float = 0.0
    read_ms: float = 0.0
    parsed_ms: float = 0.0

    @property
    def success(self) -> bool:
        return self.rcode == 0

    @classmethod
    def error(cls, cmd: str, message: str, rcode: int = -1) -> "CmdResult":
        return cls(cmd, "", message, -1, rcode)
```

### 6. Tool Result Pattern
Higher-level result with success indicator:

```python
@dataclass(frozen=True)
class ToolResult:
    cmd: str
    data: Any
    error: str
    exec_time: float

    @property
    def success(self) -> bool:
        return not self._error.strip()
```

### 7. Batch Execution Pattern
Execute multiple commands for all interfaces:

```python
def execute(self) -> None:
    """Execute all available commands."""
    for command in self.available_cmds():
        timeout = 60 if "mlxconfig" in command else 20
        self._exec(command, timeout=timeout)

def available_cmds(self) -> list[str]:
    """Get commands for all interfaces."""
    commands = []
    for interface in self._interfaces:
        for command in self._AVAILABLE_COMMANDS:
            commands.append(self._gen_cmds(interface, command))
    return commands
```

## Tool-Specific Patterns

### Ethtool Tool
```python
class EthtoolTool(Tool, ITool):
    _AVAILABLE_COMMANDS = [
        ["ethtool", CmdInputType.INTERFACE],
        ["ethtool", "-i", CmdInputType.INTERFACE],  # Driver info
        ["ethtool", "-S", CmdInputType.INTERFACE],  # Statistics
        ["ethtool", "-m", CmdInputType.INTERFACE],  # Module info
        ["ethtool", "-k", CmdInputType.INTERFACE],  # Features
    ]
```

### Mellanox Tools
```python
class MlxTool(Tool, ITool):
    _AVAILABLE_COMMANDS = [
        ["mlxlink", "-d", CmdInputType.MST_PCICONF],
        ["mlxconfig", "-d", CmdInputType.MST_PCICONF, "query"],
    ]
```

### MST Tool
```python
class MstTool(Tool, ITool):
    _AVAILABLE_COMMANDS = [
        ["mst", "status"],
        ["mst", "status", "-v"],
    ]
```

## Parser Patterns

### Parser Interface
```python
class IParser(ABC):
    _ansi_escape: ClassVar[re.Pattern] = re.compile(r"\x1b\[[0-9;]*m")

    @property
    @abstractmethod
    def name(self) -> str:
        """Get parser name."""

    @abstractmethod
    def parse(self, raw_data: str) -> Any:
        """Parse raw data into structured format."""

    @abstractmethod
    def get_result(self) -> Any:
        """Get parsed result."""
```

### ANSI Escape Handling
```python
def _log_parse(self, raw_data: str) -> None:
    clean_data = self._ansi_escape.sub("", raw_data).strip()
    preview = clean_data[:200] if len(clean_data) > 200 else clean_data
    self._logger.debug(f"[{self.name}] Parsing:\n{preview}")
```

## Error Handling Patterns

### Connection Check
```python
def _exec(self, cmd: str) -> CmdResult:
    if not self._ssh.is_connected():
        return self._ssh.get_cr_msg_connection(cmd, LogMsg.EXEC_CMD_FAIL)
    # Execute command...
```

### Result Validation
```python
def _chk_resp(self, interface: str, resp: dict, cr: CmdResult) -> None:
    if cr.success:
        resp[interface] = cr.stdout
    else:
        resp[interface] = CmdResult.error(cr.cmd, cr.stderr, cr.rcode)
```

### Timeout Handling
```python
try:
    cmd_result = self._ssh.exec_cmd(cmd, timeout=timeout)
except TimeoutError:
    cmd_result = CmdResult.error(cmd, "Command timed out")
```

## Logging Patterns

### Result Logging
```python
def _log(self, logger: logging.Logger) -> None:
    for cmd, result in self._results.items():
        if result.success:
            frame = PrettyFrame().build(f"'{cmd}' -> SUCCESS", [])
            logger.info(frame)
            logger.info(f"\n{result.stdout}\n")
        else:
            frame = PrettyFrame().build(f"'{cmd}' -> FAILED", [f"Reason: {result.stderr}"])
            logger.warning(frame)
```

### Export to JSON
```python
def _save(self, path: Path) -> None:
    try:
        with path.open("w") as f:
            json.dump(self._summarize(), f, indent=2)
    except Exception:
        self._logger.exception(f"Failed to save: {path}")
```

## Anti-Patterns to Avoid

### 1. Hardcoded Commands
```python
# BAD
result = ssh.exec_cmd("ethtool eth0")

# GOOD
result = tool._exec(self._gen_cmds("eth0", ["ethtool", CmdInputType.INTERFACE]))
```

### 2. Missing Timeout
```python
# BAD
result = ssh.exec_cmd(cmd)

# GOOD
result = ssh.exec_cmd(cmd, timeout=60)
```

### 3. Ignoring Errors
```python
# BAD
result = tool.execute()
data = result.stdout

# GOOD
result = tool.execute()
if result.success:
    data = result.stdout
else:
    logger.error(f"Command failed: {result.stderr}")
```

### 4. Direct SSH Access
```python
# BAD
class MyTool:
    def run(self):
        self._ssh.exec_cmd("my_command")

# GOOD
class MyTool(Tool, ITool):
    def run(self):
        self._exec("my_command")
```

## Implementation Guidelines

### Adding New Tools
1. Create tool class inheriting from `Tool` and `ITool`
2. Define `_AVAILABLE_COMMANDS` with command templates
3. Implement `type` property returning `ToolType` enum
4. Implement `_parse()` for output parsing
5. Register in `ToolFactory._TOOLS`

### Command Input Types
- `CmdInputType.INTERFACE`: Network interface name
- `CmdInputType.MST_PCICONF`: MST device path
- `CmdInputType.PCI_ID`: PCI device ID

### Timeout Guidelines
- Default: 20 seconds
- Configuration queries: 60 seconds
- Long-running operations: 120+ seconds

## Version History

- v1.0 (2026-01-14 00:00:00): Initial network diagnostics patterns based on codebase analysis
