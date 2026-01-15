---
title:        System File Hook Configuration
inclusion:    always
version:      1.0
last-updated: 2026-01-14 16:51:00
status:       active
---

# Kiro Hook Configuration Standards

## Purpose
Define standards for creating and maintaining Kiro hook files that enable security validation, logging, formatting, context gathering, and custom behaviors during agent lifecycle and tool execution.

## Core Principles

### Lifecycle Integration
- **Choose appropriate triggers** matching the workflow stage (agentSpawn, preToolUse, postToolUse, stop)
- **Use matchers precisely** to target specific tools rather than broad patterns
- **Handle exit codes correctly** to control tool execution flow
- **Provide meaningful output** via STDOUT/STDERR for context or warnings

### Security-First Design
- **Validate tool inputs** in preToolUse hooks before execution
- **Block dangerous operations** by returning exit code 2 with explanation
- **Audit sensitive actions** by logging tool usage in postToolUse hooks
- **Test hooks thoroughly** before deployment to avoid blocking legitimate operations

### Performance Awareness
- **Set appropriate timeouts** (default 30s) for long-running commands
- **Use caching** for expensive operations that don't change frequently
- **Keep hooks lightweight** to avoid slowing down agent interactions
- **Avoid blocking operations** in hooks that run frequently

## File Organization

### Location
**Path**: `.kiro/hooks/`
- Hook files stored alongside agent configurations
- Version controlled with project
- Named descriptively: `<purpose>.kiro.hook` or configured in agent JSON

### Hook Definition in Agent Config
```json
{
  "hooks": {
    "agentSpawn": [{"command": "script.sh"}],
    "userPromptSubmit": [{"command": "validate.sh"}],
    "preToolUse": [{"matcher": "write", "command": "check.sh"}],
    "postToolUse": [{"matcher": "shell", "command": "audit.sh"}],
    "stop": [{"command": "cleanup.sh"}]
  }
}
```

## Hook Types

### AgentSpawn
Runs when agent is activated. Use for context gathering.

```json
{
  "agentSpawn": [
    {
      "command": "git status --short",
      "timeout_ms": 5000
    }
  ]
}
```

**Exit Codes**:
- `0`: Success, STDOUT added to agent context
- Other: Warning shown to user

### UserPromptSubmit
Runs when user submits prompt. Use for input validation or context injection.

```json
{
  "userPromptSubmit": [
    {
      "command": "echo 'Project: interface-check'",
      "cache_ttl_seconds": 300
    }
  ]
}
```

**Exit Codes**:
- `0`: Success, STDOUT added to context
- Other: Warning shown to user

### PreToolUse
Runs before tool execution. Can validate and block operations.

```json
{
  "preToolUse": [
    {
      "matcher": "write",
      "command": "validate-write.sh",
      "timeout_ms": 10000
    },
    {
      "matcher": "shell",
      "command": "audit-command.sh"
    }
  ]
}
```

**Exit Codes**:
- `0`: Allow tool execution
- `2`: Block execution, STDERR returned to LLM
- Other: Warning shown, tool still executes

### PostToolUse
Runs after tool execution. Use for formatting, logging, or cleanup.

```json
{
  "postToolUse": [
    {
      "matcher": "write",
      "command": "ruff format --stdin-filename"
    },
    {
      "matcher": "@git/commit",
      "command": "notify-commit.sh"
    }
  ]
}
```

**Exit Codes**:
- `0`: Success
- Other: Warning shown (tool already executed)

### Stop
Runs when assistant finishes responding. Use for post-processing.

```json
{
  "stop": [
    {
      "command": "cargo fmt --all",
      "timeout_ms": 60000
    }
  ]
}
```

**Note**: Stop hooks do not use matchers.

## Hook Event Format

Hooks receive JSON via STDIN:

```json
{
  "hook_event_name": "preToolUse",
  "cwd": "/current/working/directory",
  "tool_name": "write",
  "tool_input": {
    "path": "/path/to/file.py",
    "content": "..."
  }
}
```

**Fields by Hook Type**:
| Field | agentSpawn | userPromptSubmit | preToolUse | postToolUse | stop |
|-------|------------|------------------|------------|-------------|------|
| hook_event_name | ✓ | ✓ | ✓ | ✓ | ✓ |
| cwd | ✓ | ✓ | ✓ | ✓ | ✓ |
| prompt | | ✓ | | | |
| tool_name | | | ✓ | ✓ | |
| tool_input | | | ✓ | ✓ | |
| tool_response | | | | ✓ | |

## Tool Matching

### Matcher Patterns
```json
{
  "preToolUse": [
    {"matcher": "write", "command": "..."},           // Exact built-in tool
    {"matcher": "@git", "command": "..."},            // All tools from MCP server
    {"matcher": "@git/status", "command": "..."},    // Specific MCP tool
    {"matcher": "*", "command": "..."},               // All tools
    {"matcher": "@builtin", "command": "..."},        // All built-in tools
    {"command": "..."}                                // No matcher = all tools
  ]
}
```

## Configuration Options

### Timeout
```json
{
  "command": "long-running-check.sh",
  "timeout_ms": 60000
}
```
Default: 30000ms (30 seconds)

### Caching
```json
{
  "command": "expensive-check.sh",
  "cache_ttl_seconds": 300
}
```
- `0`: No caching (default)
- `> 0`: Cache successful results for specified seconds
- AgentSpawn hooks are never cached

## Common Hook Patterns

### Python Formatting on Write
```json
{
  "postToolUse": [
    {
      "matcher": "write",
      "command": "ruff format"
    }
  ]
}
```

### Git Status on Spawn
```json
{
  "agentSpawn": [
    {
      "command": "git status --short && git log --oneline -5",
      "timeout_ms": 5000
    }
  ]
}
```

### Audit Logging
```json
{
  "preToolUse": [
    {
      "matcher": "shell",
      "command": "{ echo \"$(date) - Shell:\"; cat; } >> /tmp/kiro-audit.log"
    }
  ]
}
```

### Block Dangerous Commands
```bash
#!/bin/bash
# validate-shell.sh - Block dangerous shell commands
read -r input
tool_input=$(echo "$input" | jq -r '.tool_input.command // empty')

if [[ "$tool_input" =~ (rm -rf|sudo|chmod 777) ]]; then
    echo "Blocked dangerous command: $tool_input" >&2
    exit 2
fi
exit 0
```

### Test Runner on Stop
```json
{
  "stop": [
    {
      "command": "uv run pytest tests/ -q --tb=no 2>/dev/null || true",
      "timeout_ms": 120000
    }
  ]
}
```

## Best Practices

### Hook Design
1. **Single responsibility** - Each hook does one thing well
2. **Fast execution** - Keep hooks under 5 seconds when possible
3. **Graceful failures** - Handle errors without blocking workflow
4. **Clear output** - Provide actionable messages in STDERR
5. **Idempotent operations** - Safe to run multiple times

### Security Guidelines
1. **Validate inputs** - Check tool_input before allowing execution
2. **Use exit code 2** - Block dangerous operations explicitly
3. **Log sensitive actions** - Audit trail for compliance
4. **Avoid secrets in hooks** - Use environment variables
5. **Test blocking logic** - Verify legitimate operations aren't blocked

### Performance Guidelines
1. **Set timeouts** - Prevent hanging hooks
2. **Use caching** - For expensive, stable operations
3. **Minimize I/O** - Reduce file system and network calls
4. **Async where possible** - Don't block user interaction
5. **Profile slow hooks** - Identify and optimize bottlenecks

## Anti-Patterns to Avoid

### Configuration Issues
- **Missing timeouts** - Hooks that can hang indefinitely
- **Overly broad matchers** - `"*"` when specific tools intended
- **No error handling** - Scripts that fail silently
- **Hardcoded paths** - Non-portable hook scripts
- **Missing documentation** - Unclear hook purpose

### Security Problems
- **Trusting tool_input** - Not validating before use
- **Logging secrets** - Exposing credentials in audit logs
- **Weak blocking logic** - Easy to bypass restrictions
- **No exit code 2** - Warnings instead of blocks for dangerous ops
- **Untested hooks** - Deploying without verification

### Performance Issues
- **No caching** - Expensive operations on every call
- **Long timeouts** - Blocking user interaction
- **Synchronous network calls** - Slow external dependencies
- **Heavy processing** - Complex logic in hooks
- **Redundant hooks** - Multiple hooks doing same thing

## Version History

- v1.0 (2026-01-14 00:00:00): Initial version based on Kiro hooks documentation
