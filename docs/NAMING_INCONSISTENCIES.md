# Naming Convention Inconsistencies

This document lists all parameter and variable naming inconsistencies found across the Interface Check project.

## Summary

The project has several naming convention inconsistencies that should be standardized for better code maintainability and readability.

---

## 1. Command Parameter: `command` vs `cmd`

**Recommendation**: Use `command` (more explicit)

### `cmd` - 12 occurrences
- `src/ui/tabs/system.py:185` - `def _execute_command(self, cmd: str, timeout: int = 5)`
- `src/interfaces/connection.py:7` - `CmdResult.__init__(cmd: str, ...)`
- `src/interfaces/connection.py:52` - `CmdResult.error(cmd: str, stderr: str, rcode: int = -1)`
- `src/interfaces/component.py:95` - Various tool methods
- `src/core/connect.py:215` - SSH execution methods
- `src/core/tool.py:22` - `ToolResult.__init__(cmd: str, ...)`

### `command` - 17 occurrences
- `src/interfaces/component.py:47` - `def _parse(self, command: str, output: str)`
- `src/platform/software_manager.py:452` - `def _execute_command(self, command: str)`
- `src/platform/platform.py:71` - `def run_command(command: list[str], *, fail_ok: bool = False)`
- `src/platform/tools/helper.py:35` - Various helper functions
- `src/platform/tools/system.py:58` - System tool methods
- `main_eye_scan.py:350` - `def _execute_toggle(self, command: str)`

**Impact**: Medium - Affects function signatures across core modules

---

## 2. Connection Parameter: `connection` vs `conn` vs `route` vs `ssh`

**Recommendation**: Use `connection` for general SSH connections, `route` for Route objects

### `connection` - 19 occurrences
- `src/ui/components/host_selector.py:36` - `def _on_connection_change(self, connection)`
- `src/platform/hardware.py:65` - `def __init__(self, connection=None)`
- `src/platform/health.py:51` - `def __init__(self, connection)`
- Most platform and UI components use `connection`

### `route` - 1 occurrence
- `src/core/connect.py:110` - `def from_route(cls, route: Route)` (correct usage - Route type)

### `ssh` - 3 occurrences
- `src/ui/tabs/slx.py:419` - `def _get_port_id(self, ssh: SshConnection, interface: str)`
- `src/ui/tabs/slx.py:428` - `def get_interface_name(self, ssh: SshConnection, port_id: str)`
- `src/ui/tabs/slx.py:437` - `def run_eye_scan(self, ssh: SshConnection, interface_name: str, port_id: str)`

**Impact**: High - Core abstraction used throughout the project

---

## 3. Output Parameter: `output` vs `result` vs `stdout`

**Recommendation**: Use `output` for command output strings, `result` for structured return values

### `output` - 31 occurrences
- `src/ui/tabs/slx.py:478` - `def _parse_eyescan_output(self, output: str)`
- `src/interfaces/software.py:56` - `def _parse_version(self, output: str)`
- `src/interfaces/component.py:47` - `def _parse(self, command: str, output: str)`
- Most parser methods use `output`
- `main_eye_scan.py:756` - `def parse_link_status(dmesg_output: str)`

### `result` - 2 occurrences
- `src/ui/tabs/agent.py:483` - `def _handle_task_result(self, task: dict[str, Any], result: dict[str, Any])`
- `src/platform/platform.py:541` - `def log_system_test(self, test_name: str, result: bool, details: str = "")`

### `stdout` - 2 occurrences
- `src/interfaces/connection.py:7` - `CmdResult.__init__(stdout: str, ...)`
- `src/core/agent.py:295` - `def _analyze_interface_stats(self, stdout: str, issues: list[str], ...)`

**Impact**: Medium - Affects parser interfaces

---

## 4. Error Parameter: `error` vs `err` vs `stderr`

**Recommendation**: Use `error` for error messages/exceptions, `stderr` for command stderr output

### `error` - 2 occurrences
- `src/ui/tabs/agent.py:547` - `def _handle_task_error(self, task: dict[str, Any], error: str)`
- `src/core/tool.py:22` - `ToolResult.__init__(cmd: str, data: Any, error: str, ...)`

### `stderr` - 2 occurrences
- `src/interfaces/connection.py:7` - `CmdResult.__init__(stderr: str, ...)`
- `src/interfaces/connection.py:52` - `CmdResult.error(cmd: str, stderr: str, rcode: int = -1)`

**Impact**: Low - Limited usage, but important for clarity

---

## 5. Interface Parameter: `interface` vs `iface`

**Recommendation**: Use `interface` (more explicit)

### `interface` - Dominant usage
- `main_eye_scan.py:340` - `def enable_interface(self, interface_name: str)`
- `main_eye_scan.py:345` - `def disable_interface(self, interface: str)`
- `main_eye_scan.py:368` - `def run_eye_scan(self, interface: str, port_id: str)`
- `src/ui/tabs/slx.py:419` - `def _get_port_id(self, ssh: SshConnection, interface: str)`

### `iface` - Not found in function parameters
- May exist in variable names but not in function signatures

**Impact**: Low - Already mostly consistent

---

## 6. Configuration Parameter: `config` vs `cfg` vs `configuration`

**Recommendation**: Use `config` (balanced between brevity and clarity)

### `config` - Dominant usage
- `src/ui/handlers/settings.py:26` - `def build(self, config: Config)`
- `src/ui/handlers/host.py:18` - `def __init__(self, config: Config)`
- Most UI and handler classes use `config`

### `cfg` - Not found in function parameters

### `configuration` - Not found in function parameters

**Impact**: Low - Already consistent

---

## 7. CmdResult Property Names: `str_out` / `str_err` vs `stdout` / `stderr`

**Current Implementation**:
- `CmdResult.__init__` uses: `stdout`, `stderr` (constructor parameters)
- `CmdResult` properties use: `str_out`, `str_err` (property names)

**Inconsistency**: Constructor parameters don't match property names

```python
# src/interfaces/connection.py
class CmdResult:
    def __init__(self, cmd: str = "", stdout: str = "", stderr: str = "", ...):
        self._stdout = stdout
        self._stderr = stderr
    
    @property
    def str_out(self) -> str:  # Property name differs from constructor param
        return self._stdout
    
    @property
    def str_err(self) -> str:  # Property name differs from constructor param
        return self._stderr
```

**Recommendation**: Align property names with constructor parameters
- Option A: Rename properties to `stdout` and `stderr`
- Option B: Rename constructor params to `str_out` and `str_err`

**Impact**: High - Core data structure used throughout the project

---

## Recommended Standardization Plan

### Priority 1 (High Impact)
1. **CmdResult properties**: Rename `str_out` → `stdout`, `str_err` → `stderr` to match constructor
2. **Connection parameter**: Standardize to `connection: SshConnection` (change `ssh` in slx.py)

### Priority 2 (Medium Impact)
3. **Command parameter**: Standardize to `command: str` (change all `cmd` to `command`)
4. **Output parameter**: Keep `output` for raw strings, `result` for structured data

### Priority 3 (Low Impact)
5. **Error parameter**: Use `error` for exceptions, `stderr` for command output
6. **Interface parameter**: Already consistent, maintain `interface`

---

## Files Requiring Updates

### High Priority
- `src/interfaces/connection.py` - CmdResult property names
- `src/ui/tabs/slx.py` - Change `ssh` parameter to `connection`
- All files using `CmdResult.str_out` / `CmdResult.str_err` (project-wide search needed)

### Medium Priority
- `src/ui/tabs/system.py` - Change `cmd` to `command`
- `src/interfaces/component.py` - Standardize `cmd` to `command`
- `src/core/connect.py` - Standardize `cmd` to `command`
- `src/core/tool.py` - Change `cmd` to `command`

### Low Priority
- Various parser methods - Ensure consistent use of `output` vs `result`

---

## Migration Notes

When updating `CmdResult` property names:
1. Search for all usages of `.str_out` and `.str_err` in the codebase
2. Update to `.stdout` and `.stderr`
3. Update any documentation or comments referencing the old names
4. Run full test suite to ensure no breakage

**Estimated affected files**: 20-30 files (based on CmdResult usage patterns)
