---
title:        System File Agent Configuration
inclusion:    always
version:      1.0
last-updated: 2026-01-14
status:       active
---

# Custom Agent Configuration Standards

## Purpose
Define standards for creating and maintaining Kiro custom agent configurations that optimize workflow, security, and team collaboration.

## Core Principles

### Workflow Optimization
- **Pre-approve trusted tools** to eliminate permission prompts during focused work
- **Limit tool access** to reduce complexity and security risks
- **Include relevant context** through resources and hooks
- **Configure tool behavior** with specific parameters for operations

### Security-First Design
- **Start restrictive** with minimal tool access, expand as needed
- **Use specific patterns** over wildcards in allowedTools
- **Configure toolsSettings** for sensitive operations
- **Test agents** in safe environments before deployment

### Team Collaboration
- **Share configurations** via version control for consistent environments
- **Document purposes** with clear descriptions
- **Use descriptive names** that indicate agent purpose
- **Maintain local agents** for project-specific needs

## Configuration Structure

### Required Fields
```json
{
  "name": "agent-name",
  "description": "Clear description of agent purpose",
  "tools": ["read", "write", "@mcp-server"],
  "allowedTools": ["read"],
  "resources": ["file://README.md"]
}
```

### Optional Fields
```json
{
  "prompt": "file://./prompts/agent-prompt.md",
  "mcpServers": {
    "server-name": {
      "command": "server-command",
      "args": [],
      "env": {},
      "timeout": 120000
    }
  },
  "toolAliases": {
    "@server/tool": "alias"
  },
  "toolsSettings": {
    "write": {
      "allowedPaths": ["src/**"]
    }
  },
  "hooks": {
    "agentSpawn": [{"command": "git status"}]
  },
  "includeMcpJson": true,
  "model": "claude-sonnet-4"
}
```

## File Organization

### Local Agents (Project-Specific)
**Location**: `.kiro/agents/`
- Specific to current workspace
- Available only from project directory
- Version controlled with project
- Takes precedence over global agents

### Global Agents (User-Wide)
**Location**: `~/.kiro/agents/`
- Available from any directory
- Personal productivity agents
- General-purpose configurations
- Fallback when local agent not found

## Tool Configuration

### Tool References
- **Built-in tools**: `"read"`, `"write"`, `"shell"`, `"aws"`
- **All MCP server tools**: `"@server_name"`
- **Specific MCP tool**: `"@server_name/tool_name"`
- **All tools**: `"*"`
- **All built-in**: `"@builtin"`

### AllowedTools Patterns
```json
{
  "allowedTools": [
    "read",                    // Exact built-in tool
    "@git/git_status",         // Exact MCP tool
    "@fetch",                  // All tools from server
    "r*",                      // Wildcard: read, run, etc.
    "@server/read_*",          // MCP prefix pattern
    "@git-*/status"            // Server pattern
  ]
}
```

### ToolSettings Configuration
```json
{
  "toolsSettings": {
    "write": {
      "allowedPaths": ["src/**", "tests/**"]
    },
    "shell": {
      "allowedCommands": ["git status", "npm test"],
      "deniedCommands": ["rm -rf", "git push"],
      "autoAllowReadonly": true
    },
    "aws": {
      "allowedServices": ["s3", "lambda"],
      "autoAllowReadonly": true
    }
  }
}
```

## Prompt Management

### Inline Prompts
```json
{
  "prompt": "You are an expert AWS infrastructure specialist"
}
```

### File URI Prompts
```json
{
  "prompt": "file://./prompts/aws-expert.md"
}
```

**Path Resolution**:
- Relative: `"file://./prompt.md"` → same directory as agent config
- Relative parent: `"file://../shared/prompt.md"` → parent directory
- Absolute: `"file:///home/user/prompts/agent.md"` → absolute path

## Resources Configuration

All resource paths must start with `file://`:

```json
{
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md",
    "file://docs/**/*.md"
  ]
}
```

Supports:
- Specific files
- Glob patterns
- Absolute or relative paths

## Hooks Configuration

### Available Triggers
- **agentSpawn**: When agent is activated
- **userPromptSubmit**: When user submits prompt
- **preToolUse**: Before tool execution (can block)
- **postToolUse**: After tool execution
- **stop**: When assistant finishes responding

### Hook Structure
```json
{
  "hooks": {
    "agentSpawn": [
      {
        "command": "git status",
        "timeout_ms": 5000,
        "cache_ttl_seconds": 300
      }
    ],
    "preToolUse": [
      {
        "matcher": "shell",
        "command": "{ echo \"$(date) - Bash:\"; cat; } >> /tmp/audit.log"
      }
    ],
    "postToolUse": [
      {
        "matcher": "write",
        "command": "cargo fmt --all"
      }
    ]
  }
}
```

## MCP Server Configuration

```json
{
  "mcpServers": {
    "fetch": {
      "command": "fetch-server",
      "args": [],
      "env": {},
      "timeout": 120000
    },
    "git": {
      "command": "git-mcp",
      "args": [],
      "env": {
        "GIT_CONFIG_GLOBAL": "/dev/null"
      }
    },
    "remote-service": {
      "type": "http",
      "url": "https://api.example.com/mcp"
    }
  }
}
```

## Common Agent Patterns

### AWS Specialist
```json
{
  "name": "aws-specialist",
  "description": "AWS infrastructure and development tasks",
  "tools": ["read", "write", "shell", "aws"],
  "allowedTools": ["read", "aws"],
  "toolsSettings": {
    "aws": {
      "allowedServices": ["s3", "lambda", "cloudformation"]
    }
  },
  "resources": [
    "file://infrastructure/**/*.yaml",
    "file://docs/aws-setup.md"
  ]
}
```

### Development Workflow
```json
{
  "name": "dev-workflow",
  "description": "General development with Git integration",
  "mcpServers": {
    "git": {
      "command": "git-mcp-server",
      "args": []
    }
  },
  "tools": ["read", "write", "shell", "@git"],
  "allowedTools": ["read", "@git/git_status", "@git/git_log"],
  "toolAliases": {
    "@git/git_status": "status"
  }
}
```

### Code Review
```json
{
  "name": "code-review",
  "description": "Code review and quality analysis",
  "tools": ["read", "shell"],
  "allowedTools": ["read", "shell"],
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["grep", "find", "git diff", "eslint"]
    }
  },
  "resources": [
    "file://CONTRIBUTING.md",
    "file://docs/coding-standards.md"
  ]
}
```

## Best Practices

### Configuration Design
1. **Start simple** - Begin with basic tools, add complexity as needed
2. **Name clearly** - Use descriptive names indicating purpose
3. **Document usage** - Add clear descriptions for team understanding
4. **Version control** - Store configurations in project repository
5. **Test thoroughly** - Verify permissions work before sharing

### Security Guidelines
1. **Review allowedTools** carefully before deployment
2. **Use specific patterns** over broad wildcards
3. **Configure toolsSettings** for sensitive operations
4. **Test in safe environments** before production use
5. **Limit tool scope** to minimum required access

### Organization Standards
1. **Local for project-specific** - Use `.kiro/agents/` for project needs
2. **Global for general-purpose** - Use `~/.kiro/agents/` for personal tools
3. **Descriptive naming** - Clear, purpose-indicating names
4. **Prompt file organization** - Keep prompts in dedicated directory
5. **Resource documentation** - Document why resources are included

## Usage Commands

### Create Agent
```bash
# Interactive creation
kiro-cli agent create --name my-agent

# From chat session
> /agent generate
```

### Use Agent
```bash
# Start with agent
kiro-cli --agent my-agent

# Swap in session
> /agent swap
```

### List Agents
```bash
# From chat session
> /agent list
```

## Anti-Patterns to Avoid

### Configuration Issues
- **Over-permissive allowedTools** - Using `"*"` without justification
- **Missing descriptions** - No clear purpose documentation
- **Hardcoded secrets** - Credentials in configuration files
- **Unused tools** - Including tools not needed for workflow
- **Poor naming** - Generic names like "agent1" or "test"

### Security Problems
- **Broad wildcards** - `"*"` patterns without specific need
- **Missing toolsSettings** - No restrictions on sensitive operations
- **Untested configurations** - Deploying without verification
- **Shared credentials** - Embedding secrets in version control
- **Excessive permissions** - More access than required

### Organization Failures
- **No version control** - Local agents not tracked in repository
- **Missing documentation** - No explanation of agent purpose
- **Inconsistent naming** - Mixed naming conventions across agents
- **Duplicate agents** - Multiple agents for same purpose
- **Orphaned prompts** - Prompt files without corresponding agents

## Version History

- v1.0 (2026-01-14): Initial version based on Kiro custom agents documentation
