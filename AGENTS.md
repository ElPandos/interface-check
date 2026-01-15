---
title:        Custom Kiro Agents Configuration
inclusion:    always
version:      1.0
last-updated: 2026-01-15 15:25:00
status:       active
---

# Custom Agents

This document describes the custom Kiro agents configured for the interface-check project.

## Available Agents

### 1. Code Monkey Python

**Location**: `.kiro/agents/code-monkey-python.json`

**Purpose**: Fast, low-hallucination Python development with bleeding-edge practices. Includes web search, git integration, and automatic test execution on write.

**Key Features**:
- MCP servers: git, fetch, web-search, context7, find-a-domain
- Auto-runs pytest after file writes
- Access to docs, README, pyproject.toml, scripts

**Usage**:
```bash
kiro-cli --agent code-monkey-python
```

### 2. Code Monkey Rust

**Location**: `.kiro/agents/code-monkey-rust.json`

**Purpose**: Fast, correctness-first Rust development specialist with research access and web search capabilities.

**Key Features**:
- MCP servers: git, fetch, web-search, context7, find-a-domain
- Access to Cargo.toml, src/**/*.rs, research docs
- Git status and log integration

**Usage**:
```bash
kiro-cli --agent code-monkey-rust
```

### 3. Code Reviewer

**Location**: `.kiro/agents/code-reviewer.json`

**Purpose**: Code quality analysis and security-focused review specialist.

**Key Features**:
- Runs ruff, mypy, git diff commands
- Shows recent git changes on spawn
- Read-only access to src, tests, steering docs

**Usage**:
```bash
kiro-cli --agent code-reviewer
```

### 4. DevOps Infrastructure

**Location**: `.kiro/agents/devops-infrastructure.json`

**Purpose**: Docker, CI/CD, and deployment automation specialist.

**Key Features**:
- Docker and docker-compose commands
- Write access to Dockerfile, docker-compose.yml, .github/**, scripts/**
- Shows Docker version on spawn

**Usage**:
```bash
kiro-cli --agent devops-infrastructure
```

### 5. Documentation Specialist

**Location**: `.kiro/agents/documentation-specialist.json`

**Purpose**: Technical documentation creation and maintenance expert.

**Key Features**:
- Write access to docs/**, README.md, *.md
- Read access to src, docs, config files
- Counts markdown files on spawn

**Usage**:
```bash
kiro-cli --agent documentation-specialist
```

### 6. Domain Finder

**Location**: `.kiro/agents/domain-finder.json`

**Purpose**: Domain search and availability checking via find-a-domain MCP server.

**Key Features**:
- Dedicated domain search capabilities
- HTTP-based MCP server integration

**Usage**:
```bash
kiro-cli --agent domain-finder
```

### 7. Network Diagnostic Guru

**Location**: `.kiro/agents/network-diagnostic-guru.json`

**Purpose**: SSH-based network interface diagnostics and monitoring specialist for Interface Check project.

**Key Features**:
- Commands: ssh, ethtool, mlxconfig, mlxlink, mst, ping, traceroute, netstat, ss
- Access to connection code, platform tools, config files
- Lists tool files on spawn

**Usage**:
```bash
kiro-cli --agent network-diagnostic-guru
```

### 8. Project Planner Git Workflow

**Location**: `.kiro/agents/project-planner-git-workflows.json`

**Purpose**: Development workflow expert with comprehensive Git integration.

**Key Features**:
- Git MCP server with status, log, diff aliases
- Write access to src, tests, docs, config files
- Shows git status and current branch on spawn

**Usage**:
```bash
kiro-cli --agent project-planner-git-workflow
```

### 9. Project Test Runner

**Location**: `.kiro/agents/project-test-runner.json`

**Purpose**: Automated test execution and coverage analysis specialist.

**Key Features**:
- Commands: pytest, mypy, ruff, cargo test, npm test
- Read access to tests, src, config files
- Counts test files on spawn

**Usage**:
```bash
kiro-cli --agent project-test-runner
```

### 10. SSH Connection Expert

**Location**: `.kiro/agents/ssh-connection-expert.json`

**Purpose**: Multi-hop SSH connection management and automation specialist.

**Key Features**:
- Commands: ssh, ssh-keygen, ssh-add, ping, telnet, nc
- Access to connection code, config files, ~/.ssh/**
- Shows loaded SSH keys on spawn

**Usage**:
```bash
kiro-cli --agent ssh-connection-expert
```

## Creating Custom Agents

### Interactive Creation
```bash
kiro-cli agent create --name my-agent
```

### From Chat Session
```
> /agent generate
```

### Manual Creation

1. Create JSON file in `.kiro/agents/`
2. Define tools, allowedTools, and toolsSettings
3. Add relevant resources from steering documents
4. Configure hooks if needed

### Example Template
```json
{
  "name": "agent-name",
  "description": "Clear description of agent purpose",
  "tools": ["read", "write", "shell"],
  "allowedTools": ["read"],
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["specific commands"],
      "autoAllowReadonly": true
    }
  },
  "resources": [
    "file://relevant-docs.md"
  ],
  "hooks": {
    "agentSpawn": [
      {
        "command": "git status --short",
        "timeout_ms": 5000
      }
    ]
  }
}
```

## Agent Management

### List Available Agents
```
> /agent list
```

### Switch Agents
```
> /agent swap
```

### Start with Specific Agent
```bash
kiro-cli --agent agent-name
```

## Best Practices

1. **Start Restrictive**: Begin with minimal tool access, expand as needed
2. **Use Specific Patterns**: Prefer specific tool patterns over wildcards
3. **Include Relevant Resources**: Add steering documents for context
4. **Configure Tool Settings**: Set allowedPaths and allowedCommands
5. **Test Thoroughly**: Verify permissions work before sharing

## Security Guidelines

1. Review allowedTools carefully before deployment
2. Use specific patterns over broad wildcards
3. Configure toolsSettings for sensitive operations
4. Test in safe environments before production use
5. Limit tool scope to minimum required access

## Version History

- v1.0 (2026-01-15 15:25:00): Initial agent configurations for interface-check project
