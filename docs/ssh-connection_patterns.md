---
title:        SSH Connection Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# SSH Connection Patterns

## Purpose
Define patterns for SSH connection management in the interface-check project, including multi-hop connections, keepalive handling, and command execution.

## Core Patterns

### 1. Connection Interface Pattern
Abstract interface for connection types enabling polymorphic usage:

```python
class IConnection(ABC):
    @abstractmethod
    def connect(self) -> bool: ...
    
    @abstractmethod
    def disconnect(self) -> None: ...
    
    @abstractmethod
    def is_connected(self) -> bool: ...
    
    @abstractmethod
    def exec_cmd(self, cmd: str, timeout: int | None = 20) -> CmdResult: ...
```

**Benefits**: Allows swapping between SSH and local execution without code changes.

### 2. Multi-Hop Jump Host Pattern
Chain SSH connections through intermediate hosts:

```python
class SshConnection(IConnection):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        jump_hosts: list[Host] | None = None,
        keepalive_interval: int = 30,
    ): ...
    
    def _connect_via_jumps(self) -> None:
        """Establish connection through jump host chain."""
        for jump in self._jump_hosts:
            channel = self._create_jump_channel(jump)
            self._jump_clients.append(channel)
```

**Use Case**: Access isolated networks through bastion hosts.

### 3. Context Manager Pattern
Ensure proper resource cleanup:

```python
def __enter__(self) -> "SshConnection":
    self.connect()
    return self

def __exit__(self, exc_type, exc_val, exc_tb) -> None:
    self.disconnect()

# Usage
with SshConnection.from_route(route) as ssh:
    result = ssh.exec_cmd("hostname")
```

### 4. Factory Method Pattern
Create connections from configuration objects:

```python
@classmethod
def from_route(cls, route: Route) -> "SshConnection":
    return cls(
        route.target.ip,
        route.target.username,
        route.target.password.get_secret_value(),
        route.jumps,
    )
```

### 5. Keepalive Thread Pattern
Maintain connection health with background thread:

```python
def _start_keepalive(self) -> None:
    self._stop_keepalive.clear()
    self._keepalive_thread = threading.Thread(
        target=self._keepalive_loop,
        daemon=True,
    )
    self._keepalive_thread.start()

def _keepalive_loop(self) -> None:
    while not self._stop_keepalive.wait(self._keepalive_interval):
        if self.is_connected():
            self._ssh_client.get_transport().send_ignore()
```

### 6. Thread-Safe Execution Pattern
Protect command execution with locks:

```python
def exec_cmd(self, cmd: str, timeout: int | None = 20) -> CmdResult:
    with self._exec_lock:
        if not self.is_connected():
            return CmdResult.error(cmd, "Not connected")
        # Execute command...
```

### 7. Command Result Pattern
Structured result with timing metrics:

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
    
    @classmethod
    def error(cls, cmd: str, message: str) -> "CmdResult":
        return cls(cmd, "", message, -1, -1)
```

## Error Handling Patterns

### Graceful Degradation
```python
def connect(self) -> bool:
    try:
        self._ssh_client.connect(...)
        return True
    except TimeoutError:
        self._logger.exception(f"Connection timeout: {self._host}")
    except paramiko.AuthenticationException:
        self._logger.exception(f"Auth failed: {self._host}")
    except paramiko.SSHException:
        self._logger.exception(f"Protocol error: {self._host}")
    except Exception:
        self._logger.exception(f"Connection failed: {self._host}")
    
    self.disconnect()
    return False
```

### Automatic Reconnection
```python
def exec_cmd_with_retry(self, cmd: str, retries: int = 3) -> CmdResult:
    for attempt in range(retries):
        if not self.is_connected():
            self.connect()
        if self.is_connected():
            return self.exec_cmd(cmd)
        time.sleep(1)
    return CmdResult.error(cmd, "Connection failed after retries")
```

## Configuration Patterns

### Host Model
```python
class Host(BaseModel):
    ip: str = ""
    username: str = ""
    password: SecretStr = SecretStr("")
    info: str = ""
```

### Route Model
```python
class Route(BaseModel):
    summary: str
    target: Host
    jumps: list[Host] = Field(default_factory=list)
```

## Anti-Patterns to Avoid

### 1. Hardcoded Credentials
```python
# BAD
ssh = SshConnection("192.168.1.1", "admin", "password123")

# GOOD
ssh = SshConnection.from_route(config.route)
```

### 2. Missing Cleanup
```python
# BAD
ssh = SshConnection(...)
ssh.connect()
result = ssh.exec_cmd("ls")
# Connection never closed!

# GOOD
with SshConnection(...) as ssh:
    result = ssh.exec_cmd("ls")
```

### 3. Blocking Without Timeout
```python
# BAD
result = ssh.exec_cmd("long_running_command")

# GOOD
result = ssh.exec_cmd("long_running_command", timeout=300)
```

### 4. Ignoring Connection State
```python
# BAD
result = ssh.exec_cmd("hostname")

# GOOD
if ssh.is_connected():
    result = ssh.exec_cmd("hostname")
else:
    ssh.connect()
```

## Implementation Guidelines

### Connection Lifecycle
1. Create connection with configuration
2. Call `connect()` or use context manager
3. Check `is_connected()` before operations
4. Execute commands with appropriate timeouts
5. Call `disconnect()` or exit context manager

### Logging Standards
- Use LogName enums for logger names
- Use LogMsg enums for standardized messages
- Log connection events at INFO level
- Log command execution at DEBUG level
- Log errors with exception context

### Thread Safety
- Use `_exec_lock` for all command execution
- Use `threading.Event` for keepalive control
- Mark keepalive thread as daemon

## Version History

- v1.0 (2026-01-14 00:00:00): Initial SSH connection patterns based on codebase analysis
