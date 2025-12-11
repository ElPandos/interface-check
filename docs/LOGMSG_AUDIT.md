# LogMsg Usage Audit

## Summary
Analysis of logging statements across the project to identify opportunities for using LogMsg constants.

## Files Already Using LogMsg Extensively
- ✅ `main_scan.py` - Fully migrated
- ✅ `main_scan_traffic.py` - Fully migrated
- ✅ `src/core/config/__init__.py` - Fully migrated
- ✅ `src/core/config/scan.py` - Uses LogMsg in validate()
- ✅ `src/core/config/traffic.py` - Uses LogMsg in validate()

## High Priority Files for Migration

### src/core/connect/ssh.py
**Current State**: Uses hardcoded strings extensively
**Opportunities**:
- Connection messages: "Connecting to {host}", "SSH connection established"
- Error messages: "Error during disconnect", "Failed to open shell"
- Keepalive messages: "Keepalive thread started", "Keepalive loop stopped"
- Shell messages: "Opening shell on {host}", "Shell opened"

**Matching LogMsg Constants**:
- `SSH_CONN_SUCCESS`, `SSH_CONN_FAILED`, `SSH_ESTABLISHED`
- `SSH_DISCONNECTING`, `SSH_DISCONNECT_SUCCESS`
- `SHELL_OPENED`, `SHELL_OPEN_FAILED`, `SHELL_CLOSED`

### src/core/connect/local.py
**Current State**: Minimal logging with hardcoded strings
**Opportunities**:
- "Using local command execution (no SSH)"
- "Local connection closed"

**Matching LogMsg Constants**:
- `MAIN_LOCAL_EXEC`, `MAIN_LOCAL_CONN_ESTABLISHED`

### src/core/worker.py
**Current State**: Uses some LogMsg, but has hardcoded strings
**Opportunities**: Check for worker lifecycle messages

### src/core/scanner/slx.py & sut.py
**Current State**: Likely uses LogMsg already (part of scanner system)
**Action**: Verify all scanner messages use LogMsg

### src/platform/software_manager.py
**Current State**: Has extensive logging for package management
**Opportunities**: Software manager messages

**Matching LogMsg Constants**:
- `SW_MGR_*` constants (APT, YUM, package operations)

## Medium Priority Files

### src/core/traffic/iperf/*.py
**Current State**: Traffic-specific logging
**Action**: Verify traffic messages use new TRAFFIC_* constants

### src/platform/tools/*.py
**Current State**: Tool-specific logging
**Action**: Check if tool execution messages can use existing constants

### src/ui/handlers/*.py
**Current State**: UI handler logging
**Action**: Low priority - UI messages are often user-facing

## Low Priority Files
- Parser files (`src/core/parser/**/*.py`) - Parsing errors are context-specific
- UI components (`src/ui/**/*.py`) - User-facing messages
- Test files (`tests/**/*.py`) - Test-specific messages
- Examples (`examples/**/*.py`) - Example code

## Recommendation

Focus on **core infrastructure files** first:
1. `src/core/connect/ssh.py` - Most impactful (heavily used)
2. `src/core/connect/local.py` - Quick win
3. `src/core/worker.py` - Core functionality
4. `src/platform/software_manager.py` - Well-defined message set

## Migration Strategy

For each file:
1. Search for `logger.(info|error|warning|debug|exception)` with string literals
2. Match against existing LogMsg constants
3. Add new LogMsg constants if needed (group by category)
4. Replace hardcoded strings with `LogMsg.CONSTANT.value`
5. Test to ensure no regressions

## Notes
- Dynamic messages with f-strings containing variables should remain as-is
- Context-specific messages (e.g., parser errors) may not need constants
- User-facing UI messages are different from log messages
