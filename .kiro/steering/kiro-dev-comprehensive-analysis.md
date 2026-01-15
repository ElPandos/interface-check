---
title:        Kiro.Dev Comprehensive Analysis
inclusion:    always
version:      1.0
last-updated: 2026-01-15 14:45:00
status:       active
---

# Kiro.Dev Comprehensive Analysis

## Overview

Kiro CLI is an AI-powered development assistant built by Amazon Web Services that brings conversational AI capabilities directly to the terminal environment. It enables developers to build, test, deploy, and manage applications using natural language commands while maintaining full control over tool permissions, context, and workflow automation.

**Core Value Proposition**: Kiro eliminates the friction between AI assistance and development workflows by providing:
- Terminal-native AI interaction without context switching
- Semantic code understanding through LSP integration
- Persistent project knowledge via steering documents
- Specialized agents for different workflows
- Extensibility through Model Context Protocol (MCP) servers
- Automated workflows via lifecycle hooks

**Target Users**: Professional developers, DevOps engineers, system administrators, and technical teams requiring AI-assisted development with enterprise-grade security and customization.

**Platform Support**: macOS and Linux (x86_64 and ARM aarch64), with support for bash, zsh, and fish shells.

## Core Concepts

### 1. Interactive Chat Sessions

Kiro's primary interface is a conversational chat mode that maintains context across interactions:

- **Directory-based persistence**: Conversations automatically associate with working directories and can be resumed
- **Multi-line input**: `/editor` command or Ctrl+J opens system editor for complex prompts
- **Quote-reply**: `/reply` command enables structured responses to AI messages
- **Session management**: Save/load conversations as JSON files for portability
- **Model selection**: Choose between Auto (default), Claude Sonnet 4.0/4.5, Haiku 4.5, or Opus 4.5 based on task complexity

### 2. Custom Agents

Agents are specialized AI configurations that control behavior, permissions, and context:

**Purpose**: Eliminate permission prompts during focused work by pre-approving trusted tools and limiting scope to specific workflows.

**Key Components**:
- `tools`: Define available tool set (built-in + MCP servers)
- `allowedTools`: Pre-approved tools that skip permission prompts
- `toolsSettings`: Granular restrictions (allowedPaths, allowedCommands, allowedServices)
- `resources`: Auto-included context files (supports glob patterns with `file://` prefix)
- `prompt`: Custom system prompt for agent behavior
- `hooks`: Lifecycle automation (agentSpawn, preToolUse, postToolUse, stop)
- `mcpServers`: Agent-specific MCP server definitions

**Scope Hierarchy**:
- Local agents (`.kiro/agents/`): Project-specific, version-controlled
- Global agents (`~/.kiro/agents/`): User-wide, available from any directory
- Precedence: Local overrides global when names conflict

### 3. Steering System

Steering provides persistent project knowledge through markdown files, eliminating repetitive explanations:

**Three-Tier Scope**:
- Workspace (`.kiro/steering/`): Project-specific standards
- Global (`~/.kiro/steering/`): Cross-project conventions
- Team: Centralized files distributed via MDM/Group Policies
- Precedence: Workspace overrides global when conflicts exist

**Foundational Files** (automatically loaded):
- `product.md`: Product purpose, users, features, business objectives
- `tech.md`: Frameworks, libraries, tools, technical constraints
- `structure.md`: File organization, naming, imports, architecture

**Custom Steering**: API standards, testing patterns, security policies, deployment workflows, coding conventions.

**AGENTS.md Support**: Compatible with the AGENTS.md standard for agent documentation.

### 4. Model Context Protocol (MCP)

MCP extends Kiro's capabilities by enabling communication with external specialized servers:

**Server Types**:
- **Local servers**: Process-based, launched via command execution (npx, uvx, docker)
- **Remote servers**: HTTP/HTTPS endpoints for cloud-hosted services

**Configuration Hierarchy** (highest to lowest priority):
1. Agent config (`mcpServers` field in agent JSON)
2. Workspace config (`.kiro/settings/mcp.json`)
3. Global config (`~/.kiro/settings/mcp.json`)

**Tool Reference Patterns**:
- All tools from server: `@server_name`
- Specific tool: `@server_name/tool_name`
- Built-in tools: Direct name (`read`, `write`, `shell`, `aws`)

**Security Model**:
- Explicit permission required before tool execution
- Process isolation (each server runs independently)
- Local execution by default (no remote code execution)
- Environment variables for credential management (never hardcode)

### 5. Lifecycle Hooks

Hooks execute custom commands at specific lifecycle points:

**Five Hook Types**:
- **agentSpawn**: Runs when agent activates (context gathering, git status)
- **userPromptSubmit**: Runs when user submits prompt (input validation, context injection)
- **preToolUse**: Runs before tool execution (validation, can block with exit code 2)
- **postToolUse**: Runs after tool execution (formatting, logging, cleanup)
- **stop**: Runs when assistant finishes responding (post-processing, testing)

**Exit Code Behavior**:
- `0`: Success (STDOUT added to context for agentSpawn/userPromptSubmit)
- `2`: (preToolUse only) Block tool execution, STDERR returned to LLM
- Other: Warning shown to user

**Configuration Options**:
- `timeout_ms`: Default 30,000ms (30 seconds)
- `cache_ttl_seconds`: Cache successful results (0 = no caching)
- `matcher`: Tool pattern for preToolUse/postToolUse (exact, wildcard, MCP server)

### 6. Code Intelligence (LSP Integration)

Semantic code understanding through Language Server Protocol:

**Supported Languages**: TypeScript, Rust, Python, Go, Java, Ruby, C/C++

**Capabilities**:
- Search for symbols, functions, classes across codebase
- Find all references to a symbol
- Navigate to definitions
- Get compiler diagnostics and errors
- Rename symbols safely across files

**Initialization**: `/code init` in project root creates `.kiro/settings/lsp.json` configuration and starts language servers.

**Disable**: Delete `.kiro/settings/lsp.json` to turn off.

### 7. Configuration Hierarchy

Kiro uses a three-tier configuration system with clear precedence rules:

**Scope Levels** (highest to lowest priority):
1. **Agent scope**: Agent-specific configurations
2. **Project scope**: Repository-specific (`.kiro/`)
3. **Global scope**: User-wide (`~/.kiro/`)

**Configurable Components**:
- MCP servers: Agent > Project > Global
- Prompts: Project > Global
- Custom agents: Project > Global (local overrides)
- Steering: Project > Global (workspace overrides)
- Settings: Global only (no project-level overrides)

**Conflict Resolution**: Closest scope wins (most specific to least specific).

### 8. Autocomplete System

Two independent AI-powered features for command-line productivity:

**Autocomplete Dropdown**:
- Graphical menu appearing to the right of cursor
- Shows available options, subcommands, arguments
- Navigate with arrow keys, select with Tab/Enter
- Supports hundreds of tools (git, docker, npm, kubectl, terraform, aws, etc.)

**Inline Suggestions**:
- Gray "ghost text" appearing directly on command line
- Real-time completion predictions
- Accept with right arrow key or Tab
- Ignore by continuing to type

**Configuration**:
- Enable/disable independently
- Theme support (dark, light, system)
- Customization ARN support for inline suggestions

### 9. Security Model

**Permission System**:
- Explicit approval required for tool execution by default
- Pre-approval via `allowedTools` in agent configuration
- Session-level trust via `/tools trust` command
- Tool-specific restrictions via `toolsSettings`

**Credential Management**:
- Never hardcode API keys or tokens in configuration files
- Use environment variables with `${VAR_NAME}` syntax
- Exclude config files with secrets from version control
- Leverage system keychains for secure storage

**MCP Security**:
- Install servers only from trusted sources
- Process isolation (each server runs independently)
- Local execution by default
- HTTPS required for remote servers (except localhost)

### 10. Slash Commands

In-session control mechanisms for managing conversations, context, agents, and tools:

**Categories**:
- Session: `/chat`, `/save`, `/load`, `/clear`, `/quit`
- Context: `/context`, `/compact`
- Agent: `/agent`, `/model`
- Tools: `/tools`, `/mcp`, `/hooks`
- Code: `/code`
- Prompts: `/prompts`
- Input: `/editor`, `/reply`, `/paste`
- Utility: `/help`, `/usage`, `/issue`, `/logdump`, `/changelog`
- Experimental: `/experiment`, `/tangent`, `/todos`

**Keyboard Shortcuts**:
- Ctrl+C: Cancel current input
- Ctrl+J: Insert newline for multi-line prompts
- Ctrl+S: Fuzzy search commands and context files
- Ctrl+T: Toggle tangent mode (if enabled)
- ↑/↓: Navigate command history


## Architecture & Components

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kiro CLI Terminal                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat Session │  │ Autocomplete │  │ Inline Hints │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                    Core Engine Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Agent System │  │ Model Router │  │ Context Mgr  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                   Integration Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LSP Servers  │  │ MCP Servers  │  │ Built-in     │      │
│  │ (Code Intel) │  │ (Extensions) │  │ Tools        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────────┐
│                   Configuration Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Agent Configs│  │ Steering     │  │ MCP Configs  │      │
│  │ .kiro/agents/│  │ .kiro/       │  │ mcp.json     │      │
│  │              │  │ steering/    │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

**Terminal Interface Layer**:
- Chat session management with directory-based persistence
- AI-powered autocomplete dropdown menu
- Inline suggestion system with ghost text
- Keyboard shortcuts and command history

**Core Engine Layer**:
- Agent system for specialized workflows
- Model router (Auto, Sonnet, Haiku, Opus selection)
- Context manager for file inclusion and steering
- Hook execution engine for lifecycle automation
- Permission and security enforcement

**Integration Layer**:
- LSP servers for semantic code understanding
- MCP servers for external tool integration
- Built-in tools (read, write, shell, aws)
- Tool permission and trust management

**Configuration Layer**:
- Agent configurations (JSON files)
- Steering documents (markdown files)
- MCP server definitions
- Settings and preferences

### File System Structure

```
~/.kiro/                          # Global configuration
├── agents/                       # User-wide agents
│   └── *.json                    # Agent definitions
├── steering/                     # Cross-project conventions
│   ├── product.md
│   ├── tech.md
│   └── structure.md
└── settings/
    ├── cli.json                  # CLI settings
    ├── mcp.json                  # Global MCP servers
    └── lsp.json                  # LSP configuration

<project-root>/.kiro/             # Project configuration
├── agents/                       # Project-specific agents
│   └── *.json
├── steering/                     # Project standards
│   ├── product.md
│   ├── tech.md
│   ├── structure.md
│   └── *.md                      # Custom steering
└── settings/
    ├── mcp.json                  # Project MCP servers
    └── lsp.json                  # Project LSP config
```

## Key Features & Capabilities

### 1. Conversational Development

**Natural Language Interface**:
- Ask questions about code, architecture, best practices
- Request code generation, refactoring, debugging assistance
- Get explanations of complex systems
- Receive step-by-step guidance for tasks

**Context-Aware Responses**:
- Understands project structure through steering documents
- Accesses file contents via context rules
- Maintains conversation history across sessions
- Adapts to coding standards and conventions

**Multi-Turn Conversations**:
- Build on previous responses
- Clarify requirements iteratively
- Explore alternatives through tangent mode
- Quote-reply for structured feedback

### 2. Code Intelligence

**Semantic Understanding**:
- Symbol search across entire codebase
- Find all references to functions, classes, variables
- Navigate to definitions instantly
- Understand code structure and relationships

**Language Support**:
- TypeScript/JavaScript with full type awareness
- Rust with cargo integration
- Python with package understanding
- Go, Java, Ruby, C/C++ support

**Compiler Integration**:
- Real-time diagnostics and errors
- Type checking and validation
- Linting and formatting suggestions
- Safe refactoring operations

### 3. Custom Agent System

**Pre-Configured Workflows**:
- AWS infrastructure specialist
- Code reviewer with security focus
- Test runner and coverage analyzer
- Documentation writer
- Network diagnostic expert

**Permission Control**:
- Pre-approve trusted tools
- Restrict file system access
- Limit command execution
- Control AWS service access

**Context Injection**:
- Auto-load relevant documentation
- Include configuration files
- Provide domain-specific knowledge
- Execute initialization commands

### 4. MCP Server Integration

**Official Servers**:
- AWS Documentation (search and read AWS docs)
- GitHub (repository management, issues, PRs)
- Git (version control operations)
- Fetch (web content retrieval)

**Custom Servers**:
- Database integrations (PostgreSQL, MongoDB)
- Development tools (Docker, Kubernetes)
- Domain-specific APIs
- Internal company services

**Server Management**:
- Enable/disable servers dynamically
- Configure per-agent or globally
- Control tool availability
- Manage authentication

### 5. Lifecycle Hooks

**Automation Capabilities**:
- Run git status on agent spawn
- Validate commands before execution
- Format code after file writes
- Execute tests after changes
- Audit sensitive operations

**Security Enforcement**:
- Block dangerous commands
- Validate file paths
- Check permissions
- Log security-relevant actions

**Workflow Integration**:
- Trigger CI/CD pipelines
- Update documentation
- Notify team members
- Generate reports

### 6. Model Selection

**Available Models**:

| Model | Cost | Speed | Use Case |
|-------|------|-------|----------|
| Auto | 1.0x | Medium | General development (recommended) |
| Haiku 4.5 | 0.4x | 2x faster | Speed-critical, high-volume |
| Sonnet 4.0 | 1.3x | Medium | Consistent behavior |
| Sonnet 4.5 | 1.3x | Medium | Complex coding, agents |
| Opus 4.5 | 2.2x | Slower | Maximum intelligence |

**Auto Router Benefits**:
- 23% cheaper than direct Sonnet 4 usage
- Maintains Sonnet 4-level quality
- Optimizes per-task automatically
- Combines multiple frontier models

### 7. Autocomplete & Suggestions

**Dropdown Autocomplete**:
- Context-aware command completion
- Shows available subcommands and options
- Displays argument descriptions
- Supports 100+ CLI tools

**Inline Suggestions**:
- Real-time prediction as you type
- Ghost text preview
- Accept with arrow key or Tab
- Learn from usage patterns

**Supported Tools**:
- Version control: git, svn, hg
- Containers: docker, kubectl, helm
- Package managers: npm, pip, cargo, go
- Cloud: aws, gcloud, azure
- Infrastructure: terraform, ansible

### 8. Session Management

**Automatic Persistence**:
- Save every conversation turn
- Associate with working directory
- Resume previous sessions
- Maintain context across restarts

**Manual Control**:
- Save conversations to JSON files
- Load previous conversations
- Export for sharing or backup
- Custom storage backends (Git notes, cloud)

**Tangent Mode**:
- Create conversation checkpoints
- Explore side topics without disruption
- Return to main conversation flow
- Maintain separate context branches

### 9. Context Management

**Dynamic File Inclusion**:
- Add files with `/context add <path>`
- Support glob patterns (`src/**/*.py`)
- Remove unnecessary files
- View matched files and usage

**Steering Documents**:
- Automatic loading of foundational files
- Custom domain-specific guidance
- Team-wide standards distribution
- Version-controlled conventions

**Context Window Optimization**:
- Compact command to summarize
- Selective file inclusion
- Agent-scoped context rules
- Performance-aware loading

### 10. Enterprise Features

**Proxy Support**:
- HTTP/HTTPS proxy configuration
- Authenticated proxy handling
- NO_PROXY domain bypass
- Corporate firewall compatibility

**MCP Governance** (Pro tier):
- Centralized MCP server control
- Allow-list enforcement via registry
- Organization-wide policies
- Account-level overrides

**IAM Integration**:
- IAM Identity Center support
- AWS Builder ID authentication
- Role-based access control
- Audit logging capabilities


## Usage Patterns & Best Practices

### Getting Started

**Installation**:
```bash
# macOS/Linux one-line install
curl -fsSL https://cli.kiro.dev/install | bash

# Verify installation
kiro-cli --version
kiro-cli doctor
```

**First Session**:
```bash
# Start chat
kiro-cli

# Start with specific agent
kiro-cli --agent code-monkey-python

# Resume previous conversation
kiro-cli chat --resume
```

### Agent Development Workflow

**Creating Specialized Agents**:
```bash
# Interactive creation
> /agent generate

# Manual creation
# Create .kiro/agents/my-agent.json with configuration
```

**Agent Configuration Pattern**:
```json
{
  "name": "backend-specialist",
  "description": "Backend development with database access",
  "tools": ["read", "write", "shell", "@postgres"],
  "allowedTools": ["read", "@postgres/query"],
  "toolsSettings": {
    "write": {"allowedPaths": ["src/backend/**", "tests/**"]},
    "shell": {"allowedCommands": ["npm test", "npm run lint"]}
  },
  "resources": [
    "file://README.md",
    "file://.kiro/steering/**/*.md"
  ],
  "hooks": {
    "agentSpawn": [{"command": "git status --short"}],
    "postToolUse": [{
      "matcher": "write",
      "command": "prettier --write"
    }]
  }
}
```

### Context Management Patterns

**Project-Specific Context**:
```bash
# Add relevant files
> /context add "src/**/*.ts"
> /context add "tests/**/*.test.ts"
> /context add "package.json"

# View current context
> /context show

# Remove unnecessary patterns
> /context remove "node_modules/**"
```

**Steering Document Organization**:
```
.kiro/steering/
├── product.md              # Product vision and goals
├── tech.md                 # Technology stack
├── structure.md            # Project organization
├── api-standards.md        # REST API conventions
├── testing-patterns.md     # Test strategies
└── security-policies.md    # Security requirements
```

### MCP Server Integration

**Local Server Setup**:
```json
{
  "mcpServers": {
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"],
      "env": {"GIT_CONFIG_GLOBAL": "/dev/null"}
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

**Remote Server with Authentication**:
```json
{
  "mcpServers": {
    "company-api": {
      "url": "https://api.company.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    }
  }
}
```

### Hook Automation Patterns

**Code Formatting on Write**:
```json
{
  "hooks": {
    "postToolUse": [{
      "matcher": "write",
      "command": "ruff format --stdin-filename"
    }]
  }
}
```

**Security Validation**:
```json
{
  "hooks": {
    "preToolUse": [{
      "matcher": "shell",
      "command": "validate-command.sh"
    }]
  }
}
```

**Test Execution on Stop**:
```json
{
  "hooks": {
    "stop": [{
      "command": "pytest tests/ -q",
      "timeout_ms": 120000
    }]
  }
}
```

### Best Practices

**Security**:
1. Start with minimal tool permissions, expand as needed
2. Use specific patterns in `allowedTools` (avoid wildcards)
3. Never hardcode credentials (use `${ENV_VAR}` syntax)
4. Review MCP server sources before installation
5. Configure `toolsSettings` for sensitive operations

**Performance**:
1. Use caching for expensive hook operations
2. Set appropriate timeouts (default 30s)
3. Keep hooks lightweight (<5s execution time)
4. Use selective context inclusion (avoid large globs)
5. Leverage Auto model for cost optimization

**Organization**:
1. Version control `.kiro/` directory with project
2. Use descriptive agent names indicating purpose
3. Document agent purposes in descriptions
4. Maintain separate prompts directory
5. Keep steering files focused (one domain per file)

**Workflow Optimization**:
1. Create agents for common workflows
2. Pre-approve frequently used tools
3. Include relevant steering documents
4. Use tangent mode for exploratory work
5. Save important conversations for reference

## Configuration & Setup

### Installation Methods

**macOS**:
```bash
# One-line installer
curl -fsSL https://cli.kiro.dev/install | bash

# Homebrew (alternative)
brew install kiro-cli
```

**Linux**:
```bash
# One-line installer
curl -fsSL https://cli.kiro.dev/install | bash

# AppImage (portable)
curl -O https://desktop-release.q.us-east-1.amazonaws.com/latest/kirocli-x86_64-linux.appimage
chmod +x kirocli-x86_64-linux.appimage
./kirocli-x86_64-linux.appimage

# Ubuntu .deb
curl -O https://desktop-release.q.us-east-1.amazonaws.com/latest/kiro-cli_amd64.deb
sudo dpkg -i kiro-cli_amd64.deb
```

**System Requirements**:
- 64-bit x86_64 or ARM aarch64
- glibc 2.34+ (or musl variant for older systems)
- bash, zsh, or fish shell
- curl and unzip utilities

### Initial Configuration

**Authentication**:
```bash
# First launch triggers browser authentication
kiro-cli

# Manual login if needed
kiro-cli login
```

**Shell Integration**:
```bash
# Verify autocomplete setup
kiro-cli doctor

# Configure autocomplete
kiro-cli settings autocomplete.disable false

# Configure inline suggestions
kiro-cli inline enable

# Set theme
kiro-cli theme dark
```

**Proxy Configuration** (Enterprise):
```bash
# Set environment variables
export HTTPS_PROXY=http://proxy.company.com:8080
export NO_PROXY=localhost,.company.com

# Launch Kiro
kiro-cli
```

### Agent Configuration

**File Location**:
- Global: `~/.kiro/agents/agent-name.json`
- Local: `.kiro/agents/agent-name.json`

**Required Fields**:
```json
{
  "name": "agent-name",
  "description": "Clear description of purpose",
  "tools": ["read", "write"],
  "allowedTools": ["read"]
}
```

**Optional Fields**:
```json
{
  "prompt": "file://./prompts/agent-prompt.md",
  "model": "claude-sonnet-4",
  "resources": ["file://README.md"],
  "toolsSettings": {
    "write": {"allowedPaths": ["src/**"]}
  },
  "hooks": {
    "agentSpawn": [{"command": "git status"}]
  },
  "mcpServers": {
    "git": {"command": "uvx", "args": ["mcp-server-git"]}
  },
  "includeMcpJson": true
}
```

### Steering Configuration

**Foundational Files** (`.kiro/steering/`):

**product.md**:
```markdown
# Product Foundation

## Vision
[Product purpose and goals]

## Target Users
[Primary user personas]

## Core Capabilities
[Key features and workflows]
```

**tech.md**:
```markdown
# Technology Foundation

## Runtime Stack
[Languages, frameworks, libraries]

## Development Tools
[Build tools, linters, formatters]

## Key Dependencies
[Critical packages and versions]
```

**structure.md**:
```markdown
# Structure Foundation

## Directory Layout
[File organization]

## Key Components
[Architecture overview]

## Key Patterns
[Design patterns used]
```

### MCP Server Configuration

**Configuration File** (`.kiro/settings/mcp.json`):
```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {"FASTMCP_LOG_LEVEL": "ERROR"}
    },
    "github": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
               "ghcr.io/github/github-mcp-server"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
    }
  }
}
```

**Server Management**:
```bash
# Add server via CLI
kiro-cli mcp add \
  --name "server-name" \
  --scope global \
  --command "uvx" \
  --args "package@version"

# View loaded servers
> /mcp

# Enable/disable in config
{
  "mcpServers": {
    "server-name": {
      "disabled": true
    }
  }
}
```

### LSP Configuration

**Initialization**:
```bash
# Initialize in project root
> /code init

# Force restart
> /code init -f

# Check status
> /code status
```

**Configuration File** (`.kiro/settings/lsp.json`):
- Created automatically by `/code init`
- Customizable per project
- Delete file to disable LSP

**Supported Languages**:
- TypeScript/JavaScript
- Rust
- Python
- Go
- Java
- Ruby
- C/C++


## API & Integration

### Built-in Tools

**File Operations**:
- `read`: Read file contents
- `write`: Create or modify files
- `fs_read`: Advanced file reading with modes
- `fs_write`: Advanced file writing with operations

**Command Execution**:
- `shell`: Execute shell commands
- `execute_bash`: Run bash scripts

**AWS Integration**:
- `aws`: AWS CLI operations
- `use_aws`: Advanced AWS API calls

**Code Intelligence**:
- `code`: LSP-powered semantic analysis
- `grep`: Fast text pattern search
- `glob`: File and directory discovery

**Utility**:
- `todo_list`: Task management
- `use_subagent`: Delegate to specialized agents
- `delegate`: Asynchronous task execution (deprecated)

### MCP Server Integration

**Official MCP Servers**:

1. **AWS Documentation**:
   - Search AWS documentation across all services
   - Read documentation pages in markdown
   - Get content recommendations
   - Package: `awslabs.aws-documentation-mcp-server@latest`

2. **GitHub**:
   - Repository management (files, commits, branches)
   - Issue and pull request operations
   - Code search capabilities
   - Docker image: `ghcr.io/github/github-mcp-server`

3. **Git**:
   - Version control operations
   - Status, log, diff, commit
   - Package: `mcp-server-git`

4. **Fetch**:
   - Web content retrieval
   - HTTP/HTTPS requests
   - Package: `mcp-server-fetch`

**Custom Server Development**:
- Python: Use FastMCP or MCP SDK
- Node.js: Use @modelcontextprotocol/sdk
- Protocol: [MCP Specification 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18)

**Server Configuration Structure**:
```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["arg1", "arg2"],
      "env": {"VAR": "${VALUE}"},
      "timeout": 120000,
      "disabled": false,
      "autoApprove": ["tool1"],
      "disabledTools": ["tool2"]
    }
  }
}
```

### Tool Reference Patterns

**Built-in Tools**:
- Direct name: `"read"`, `"write"`, `"shell"`, `"aws"`
- All built-in: `"@builtin"`

**MCP Tools**:
- All from server: `"@git"`
- Specific tool: `"@git/git_status"`
- All tools: `"*"`

**Pattern Matching** (allowedTools):
- Exact: `"read"`, `"@git/status"`
- Wildcard: `"r*"`, `"*_bash"`, `"?ead"`
- Server pattern: `"@git-*/status"`
- Tool prefix: `"@server/read_*"`

### Hook Integration

**Hook Event Format** (JSON via STDIN):
```json
{
  "hook_event_name": "preToolUse",
  "cwd": "/current/working/directory",
  "tool_name": "write",
  "tool_input": {
    "path": "/path/to/file.py",
    "content": "..."
  },
  "tool_response": {...}
}
```

**Exit Code Contract**:
- `0`: Success (STDOUT captured for agentSpawn/userPromptSubmit)
- `2`: Block execution (preToolUse only, STDERR to LLM)
- Other: Warning shown, execution continues

**Hook Configuration**:
```json
{
  "hooks": {
    "agentSpawn": [
      {"command": "git status", "timeout_ms": 5000}
    ],
    "preToolUse": [
      {"matcher": "write", "command": "validate.sh"}
    ],
    "postToolUse": [
      {"matcher": "write", "command": "format.sh"}
    ],
    "stop": [
      {"command": "test.sh", "timeout_ms": 60000}
    ]
  }
}
```

### Slash Command API

**Session Management**:
- `/chat resume` - Resume previous conversation
- `/save [path]` - Save conversation to JSON
- `/load [path]` - Load conversation from JSON
- `/clear` - Clear current conversation
- `/quit` - Exit Kiro CLI

**Context Management**:
- `/context add <pattern>` - Add files to context
- `/context remove <pattern>` - Remove files from context
- `/context show` - Display current context
- `/compact` - Summarize conversation

**Agent Management**:
- `/agent list` - Show available agents
- `/agent swap` - Switch to different agent
- `/agent generate` - Create new agent with AI
- `/agent set-default` - Set persistent default agent
- `/agent schema` - View agent configuration structure

**Tool Management**:
- `/tools` - List available tools
- `/tools trust <tool>` - Trust tool for session
- `/tools untrust <tool>` - Untrust tool
- `/tools trust-all` - Trust all tools
- `/tools reset` - Reset to defaults
- `/tools schema <tool>` - View tool input schema

**Code Intelligence**:
- `/code init` - Initialize LSP servers
- `/code init -f` - Force restart LSP
- `/code status` - View LSP status
- `/code logs` - View LSP logs

**MCP Management**:
- `/mcp` - List loaded MCP servers
- `/mcp add` - Add MCP server

**Input Methods**:
- `/editor` - Open editor for multi-line input
- `/reply` - Reply to previous message with editor
- `/paste` - Paste multi-line content

**Model Selection**:
- `/model` - View current model and options
- `/model set-current-as-default` - Persist model choice

### Custom Storage Backends

**Save Script Contract**:
```bash
#!/bin/bash
# Receives JSON via stdin
# Outputs confirmation to stderr
# Exit code 0 for success

cat > /path/to/storage
echo "Saved successfully" >&2
exit 0
```

**Load Script Contract**:
```bash
#!/bin/bash
# Outputs JSON to stdout
# Exit code 0 for success

cat /path/to/storage
exit 0
```

**Configuration**:
```bash
kiro-cli settings chat.saveScript "/path/to/save.sh"
kiro-cli settings chat.loadScript "/path/to/load.sh"
```

## Common Pitfalls & Anti-Patterns

### Configuration Issues

**Agent Configuration**:
- ❌ Over-permissive `allowedTools` using `"*"` without justification
- ❌ Missing descriptions making agents hard to identify
- ❌ Hardcoded secrets in configuration files
- ❌ Unused tools cluttering configuration
- ❌ Poor naming like "agent1" or "test"
- ✅ Start restrictive, expand as needed
- ✅ Use specific tool patterns
- ✅ Document agent purposes clearly
- ✅ Use environment variables for secrets

**Hook Configuration**:
- ❌ Missing timeouts causing hangs
- ❌ Overly broad matchers (`"*"` when specific tools intended)
- ❌ No error handling in scripts
- ❌ Hardcoded paths making hooks non-portable
- ❌ Missing documentation of hook purpose
- ✅ Set appropriate timeouts (default 30s)
- ✅ Use specific matchers
- ✅ Handle errors gracefully
- ✅ Use relative paths or environment variables

**MCP Configuration**:
- ❌ Hardcoded API keys in configuration
- ❌ Invalid JSON syntax (missing commas, brackets)
- ❌ Commands not in PATH
- ❌ Missing environment variables
- ❌ Untrusted server sources
- ✅ Use `${ENV_VAR}` for credentials
- ✅ Validate JSON syntax
- ✅ Verify command availability
- ✅ Set environment variables before launch
- ✅ Review server sources before installation

### Security Problems

**Credential Management**:
- ❌ Storing API keys in version control
- ❌ Hardcoding passwords in agent configs
- ❌ Logging secrets in hook output
- ❌ Sharing configurations with embedded credentials
- ✅ Use environment variables exclusively
- ✅ Add config files with secrets to .gitignore
- ✅ Sanitize hook output
- ✅ Document required environment variables

**Permission Control**:
- ❌ Trusting all tools without review
- ❌ Weak blocking logic in preToolUse hooks
- ❌ No validation of tool inputs
- ❌ Broad file system access patterns
- ✅ Review tool permissions carefully
- ✅ Use exit code 2 to block dangerous operations
- ✅ Validate inputs before execution
- ✅ Use specific `allowedPaths` patterns

**MCP Security**:
- ❌ Installing servers from unknown sources
- ❌ Granting broad network access
- ❌ Skipping SSL certificate validation
- ❌ No monitoring of server activity
- ✅ Install only from trusted sources
- ✅ Limit network access where possible
- ✅ Use HTTPS for remote servers
- ✅ Review logs regularly

### Performance Issues

**Hook Performance**:
- ❌ No caching for expensive operations
- ❌ Long timeouts blocking user interaction
- ❌ Synchronous network calls in hooks
- ❌ Heavy processing in frequently-called hooks
- ❌ Redundant hooks doing same work
- ✅ Use `cache_ttl_seconds` for expensive ops
- ✅ Set reasonable timeouts (<5s when possible)
- ✅ Avoid network calls in hooks
- ✅ Keep hooks lightweight
- ✅ Consolidate related operations

**Context Management**:
- ❌ Including entire directories with `**/*`
- ❌ Not removing unnecessary files
- ❌ Loading large binary files
- ❌ Duplicate file patterns
- ✅ Use specific glob patterns
- ✅ Remove files when no longer needed
- ✅ Exclude binary files
- ✅ Review context with `/context show`

**Model Selection**:
- ❌ Using Opus for simple tasks
- ❌ Using Haiku for complex reasoning
- ❌ Not leveraging Auto router
- ❌ Ignoring cost implications
- ✅ Use Auto as default
- ✅ Reserve Opus for maximum intelligence needs
- ✅ Use Haiku for speed-critical work
- ✅ Monitor credit consumption

### Organization Failures

**File Organization**:
- ❌ No version control for `.kiro/` directory
- ❌ Missing documentation of agent purposes
- ❌ Inconsistent naming conventions
- ❌ Duplicate agents for same purpose
- ❌ Orphaned prompt files
- ✅ Version control project configurations
- ✅ Document agent purposes in descriptions
- ✅ Use consistent naming conventions
- ✅ Consolidate duplicate agents
- ✅ Organize prompts in dedicated directory

**Steering Documents**:
- ❌ Mixing multiple domains in one file
- ❌ No version history tracking
- ❌ Outdated information not updated
- ❌ Missing context for decisions
- ✅ One domain per file
- ✅ Update version history
- ✅ Review during architecture changes
- ✅ Document rationale, not just rules

**Team Collaboration**:
- ❌ Not sharing agent configurations
- ❌ Inconsistent environments across team
- ❌ No documentation of setup process
- ❌ Missing onboarding guide
- ✅ Version control shared configurations
- ✅ Document required environment variables
- ✅ Provide setup instructions
- ✅ Create onboarding documentation


## Advanced Topics

### MCP Governance (Enterprise)

**Purpose**: Centralized control over MCP server access for organizations using IAM Identity Center (Pro tier only).

**Control Levels**:
- Complete MCP disable/enable toggle
- Allow-list enforcement via MCP registry (Q subscription users)
- Organization-level defaults with account-level overrides
- Separate profiles for Kiro and Q Developer subscriptions

**Registry-Based Allow-listing**:
- JSON-based server definitions served over HTTPS
- Supports remote (HTTP) and local (stdio) MCP servers
- 24-hour synchronization cycle
- Automatic server termination if removed from registry
- Version enforcement with automatic relaunching

**Registry File Structure**:
```json
{
  "mcpServers": {
    "approved-server": {
      "name": "approved-server",
      "version": "1.0.0",
      "description": "Approved MCP server",
      "transport": {
        "type": "streamable-http",
        "url": "https://mcp.example.com"
      }
    }
  }
}
```

**Deployment Requirements**:
- Pro-tier subscription required
- IAM Identity Center sign-in mandatory
- Valid SSL certificates (no self-signed)
- Package runners (npx/uvx/docker) pre-installed for local servers

**Limitations**:
- Client-side enforcement only (technically circumventable)
- Allow-list feature only for Q subscription users
- Kiro subscription users can only disable/enable MCP entirely
- No built-in audit logging of MCP usage
- No granular per-user controls (only account/org level)

### Delegate Feature (Deprecated)

**Note**: Being replaced by official subagents tool. Use subagents for new workflows.

**Purpose**: Launch and manage asynchronous task processes in background.

**Key Capabilities**:
- Launch background tasks using natural language
- Run parallel chat sessions with specialized agents
- Monitor task progress independently
- Continue main conversation without blocking

**Enabling**:
```bash
kiro-cli settings chat.enableDelegate true
# or use /experiment command
```

**Use Cases**:
- Long-running operations (test suites, builds, analysis)
- Independent tasks not requiring user input
- Parallel work (multiple simultaneous tasks)
- Background monitoring (continuous checks)

**Limitations**:
- Limited concurrent tasks
- Tasks cannot communicate with main conversation
- Session-scoped persistence (results may not survive restarts)
- Performance impact with many concurrent tasks

### Tangent Mode

**Purpose**: Create conversation checkpoints to explore side topics without disrupting main flow.

**Enabling**:
```bash
> /experiment
# Select tangent mode
```

**Usage**:
```bash
# Enter tangent mode
> /tangent

# Explore side topic
> [side investigation]

# Exit tangent mode (return to main conversation)
> /tangent
```

**Keyboard Shortcut**: Ctrl+T (if enabled)

**Benefits**:
- Maintain separate context branches
- Explore alternatives without polluting main conversation
- Return to main flow seamlessly
- Preserve checkpoint state

### Custom Prompt Templates

**Purpose**: Reusable prompt templates from MCP servers or local storage.

**MCP Integration**:
```bash
# List available prompts
> /prompts

# Use prompt with shorthand
> @prompt-name [arg]
```

**Local Prompts**:
- Create custom prompts in `.kiro/prompts/`
- Edit and remove prompts via `/prompts` command
- Share prompts across team via version control

### Advanced Hook Patterns

**Audit Logging**:
```json
{
  "preToolUse": [{
    "matcher": "shell",
    "command": "{ echo \"$(date) - Shell:\"; cat; } >> /tmp/kiro-audit.log"
  }]
}
```

**Block Dangerous Commands**:
```bash
#!/bin/bash
# validate-shell.sh
read -r input
tool_input=$(echo "$input" | jq -r '.tool_input.command // empty')

if [[ "$tool_input" =~ (rm -rf|sudo|chmod 777) ]]; then
    echo "Blocked dangerous command: $tool_input" >&2
    exit 2
fi
exit 0
```

**Conditional Formatting**:
```bash
#!/bin/bash
# format-python.sh
read -r input
file_path=$(echo "$input" | jq -r '.tool_input.path // empty')

if [[ "$file_path" == *.py ]]; then
    ruff format "$file_path"
fi
exit 0
```

### Advanced Agent Patterns

**Multi-Server Integration**:
```json
{
  "mcpServers": {
    "github": {"command": "github-mcp", "args": []},
    "gitlab": {"command": "gitlab-mcp", "args": []}
  },
  "toolAliases": {
    "@github/get_issues": "github_issues",
    "@gitlab/get_issues": "gitlab_issues"
  }
}
```

**Environment-Specific Agents**:
```json
{
  "name": "prod-deploy",
  "description": "Production deployment specialist",
  "tools": ["read", "shell", "aws"],
  "allowedTools": ["read"],
  "toolsSettings": {
    "shell": {
      "allowedCommands": ["kubectl apply", "helm upgrade"],
      "deniedCommands": ["kubectl delete", "helm delete"]
    },
    "aws": {
      "allowedServices": ["s3", "cloudformation"],
      "autoAllowReadonly": true
    }
  },
  "hooks": {
    "preToolUse": [{
      "matcher": "shell",
      "command": "validate-prod-command.sh"
    }]
  }
}
```

### Troubleshooting Advanced Issues

**Agent Loading Problems**:
```bash
# Check agent precedence
> /agent list

# Verify agent configuration
> /agent schema

# Test with default agent first
kiro-cli

# Check file permissions
ls -la .kiro/agents/
```

**MCP Server Issues**:
```bash
# Verify server status
> /mcp

# Check command availability
which uvx
which docker

# Test server independently
uvx mcp-server-git

# Review logs
> /code logs -l DEBUG
```

**LSP Troubleshooting**:
```bash
# Force restart
> /code init -f

# Check status
> /code status

# View detailed logs
> /code logs -l DEBUG -n 100

# Export logs for analysis
> /code logs -p /tmp/lsp-logs.json
```

**Context Window Issues**:
```bash
# View current usage
> /context show

# Compact conversation
> /compact

# Remove unnecessary files
> /context remove "**/*.test.ts"

# Use more specific patterns
> /context add "src/core/**/*.ts"
```

### Performance Optimization

**Hook Caching Strategy**:
```json
{
  "hooks": {
    "agentSpawn": [{
      "command": "expensive-check.sh",
      "cache_ttl_seconds": 300,
      "timeout_ms": 10000
    }]
  }
}
```

**Context Optimization**:
- Use specific glob patterns instead of `**/*`
- Exclude test files unless needed
- Remove files after use
- Leverage agent-scoped context rules

**Model Selection Strategy**:
- Use Auto for general development (23% cheaper)
- Use Haiku for speed-critical, high-volume work
- Reserve Sonnet for complex coding and agents
- Save Opus for maximum intelligence requirements

### Integration with CI/CD

**Git Notes Storage**:
```bash
# Save script
#!/bin/bash
COMMIT=$(git rev-parse HEAD)
git notes --ref=kiro/notes add -F <(cat) "$COMMIT" --force
echo "Saved to git notes" >&2

# Load script
#!/bin/bash
COMMIT=$(git rev-parse HEAD)
git notes --ref=kiro/notes show "$COMMIT"
```

**Automated Testing Hook**:
```json
{
  "hooks": {
    "stop": [{
      "command": "npm test -- --silent",
      "timeout_ms": 120000
    }]
  }
}
```

**Deployment Validation**:
```json
{
  "hooks": {
    "preToolUse": [{
      "matcher": "aws",
      "command": "validate-aws-operation.sh"
    }]
  }
}
```

## Endpoint Reference

### Depth 0: Core Documentation (1 page)
- https://kiro.dev/docs/cli - Main CLI documentation hub

### Depth 1: Primary Features (7 pages)
- https://kiro.dev/docs/cli/autocomplete - Autocomplete and inline suggestions
- https://kiro.dev/docs/cli/chat - Interactive chat sessions
- https://kiro.dev/docs/cli/custom-agents - Custom agent system
- https://kiro.dev/docs/cli/hooks - Lifecycle hooks
- https://kiro.dev/docs/cli/installation - Installation methods
- https://kiro.dev/docs/cli/mcp - Model Context Protocol integration
- https://kiro.dev/docs/cli/steering - Steering system

### Depth 2: Detailed Topics (13 pages)
- https://kiro.dev/docs/cli/chat/configuration - Configuration hierarchy
- https://kiro.dev/docs/cli/chat/model-selection - Model selection and costs
- https://kiro.dev/docs/cli/chat/responding - Reply command
- https://kiro.dev/docs/cli/custom-agents/configuration-reference - Agent config reference
- https://kiro.dev/docs/cli/custom-agents/creating - Creating custom agents
- https://kiro.dev/docs/cli/custom-agents/troubleshooting - Agent troubleshooting
- https://kiro.dev/docs/cli/experimental/delegate - Delegate feature (deprecated)
- https://kiro.dev/docs/cli/mcp/configuration - MCP configuration
- https://kiro.dev/docs/cli/mcp/examples - MCP server examples
- https://kiro.dev/docs/cli/mcp/governance - MCP governance (enterprise)
- https://kiro.dev/docs/cli/mcp/security - MCP security model
- https://kiro.dev/docs/cli/reference/slash-commands - Slash command reference
- https://kiro.dev/docs/cli/reference/supported-environments - Supported environments

## Sources & References

1. https://kiro.dev/docs/cli
2. https://kiro.dev/docs/cli/autocomplete
3. https://kiro.dev/docs/cli/chat
4. https://kiro.dev/docs/cli/chat/configuration
5. https://kiro.dev/docs/cli/chat/model-selection
6. https://kiro.dev/docs/cli/chat/responding
7. https://kiro.dev/docs/cli/custom-agents
8. https://kiro.dev/docs/cli/custom-agents/configuration-reference
9. https://kiro.dev/docs/cli/custom-agents/creating
10. https://kiro.dev/docs/cli/custom-agents/troubleshooting
11. https://kiro.dev/docs/cli/experimental/delegate
12. https://kiro.dev/docs/cli/hooks
13. https://kiro.dev/docs/cli/installation
14. https://kiro.dev/docs/cli/mcp
15. https://kiro.dev/docs/cli/mcp/configuration
16. https://kiro.dev/docs/cli/mcp/examples
17. https://kiro.dev/docs/cli/mcp/governance
18. https://kiro.dev/docs/cli/mcp/security
19. https://kiro.dev/docs/cli/reference/slash-commands
20. https://kiro.dev/docs/cli/reference/supported-environments
21. https://kiro.dev/docs/cli/steering

## Version History

- v1.0 (2026-01-15 14:45:00): Initial comprehensive analysis from 21 pages of Kiro CLI documentation
