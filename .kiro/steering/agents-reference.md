---
title: Agents Reference Guide
inclusion: always
version: 1.2
last-updated: 2026-01-15 16:03:00
status: active
---

# Agents Reference Guide

This document provides a comprehensive reference for all custom Kiro agents configured for the interface-check project.

## Agent Overview

| Agent Name | Description | MCP Servers | Prompt File |
|------------|-------------|-------------|-------------|
| backend-dev | General backend development specialist | git, fetch, web-search | file://../prompts/agents/backend-dev.md |
| frontend-dev | General frontend development specialist | git, fetch, web-search | file://../prompts/agents/frontend-dev.md |
| test-dev | Multi-language test execution specialist | None | file://../prompts/agents/test-dev.md |
| ssh-connection-expert | Multi-hop SSH connection management | None | file://../prompts/agents/ssh-connection-expert.md |
| project-test-runner | Automated test execution and coverage | None | file://../prompts/agents/project-test-runner.md |
| project-planner-git-workflow | Development workflow with Git integration | git | file://../prompts/agents/project-planner-git-workflows.md |
| network-diagnostic-guru | SSH-based network interface diagnostics | None | file://../prompts/agents/network-diagnostic-guru.md |
| hook-tester | Minimal agent for testing hooks | None | None |
| documentation-specialist | Technical documentation expert | None | file://../prompts/agents/documentation-specialist.md |
| domain-finder | Domain search capabilities | find-a-domain | file://../prompts/agents/domain-finder.md |
| devops-infrastructure | Docker, CI/CD, deployment specialist | None | file://../prompts/agents/devops-infrastructure.md |
| code-reviewer | Code quality analysis and security review | None | file://../prompts/agents/code-reviewer.md |
| code-monkey-rust | Fast, correctness-first Rust development | git, fetch, web-search, context7, find-a-domain | file://../prompts/agents/code-monkey-rust.md |
| code-monkey-python | Fast, correctness-first Python development | git, fetch, web-search, context7, find-a-domain | file://../prompts/agents/code-monkey-python.md |

## Detailed Agent Specifications

### backend-dev

**Description**: General backend development specialist supporting Python, Node.js, Rust, Go, and Java. Focuses on API design, security, performance, and scalable architecture.

**Tools**: `["*"]`
**Allowed Tools**: `["read", "@git/git_status", "@git/git_log", "@fetch"]`

**Tool Settings**:
- **write**: Allowed paths include `src/**/*.py`, `src/**/*.ts`, `src/**/*.js`, `src/**/*.rs`, `src/**/*.go`, `src/**/*.java`, `tests/**`, `api/**`, `routes/**`, `controllers/**`, `services/**`, `models/**`, `schemas/**`, `migrations/**`
- **shell**: Allowed commands include `pytest`, `cargo test`, `go test`, `npm test`, `mvn test`, `cargo build`, `go build`, `npm run build`

**MCP Servers**:
- **git**: `git-mcp` with 120s timeout
- **fetch**: `fetch3.1` with 120s timeout  
- **web-search**: Brave Search API with 120s timeout

**Tool Aliases**:
- `@git/git_status` → `status`
- `@git/git_log` → `log`

**Resources**: API design docs, security patterns, error handling, code quality, testing, performance optimization, Python/Rust patterns, README, pyproject.toml, Cargo.toml, package.json, go.mod

**Hooks**:
- **agentSpawn**: Shows git status and recent commits
- **postToolUse**: Auto-formats Python files with ruff after write operations

### frontend-dev

**Description**: General frontend development specialist supporting React, Vue, Angular, Svelte, and vanilla JS/TS. Focuses on accessibility, performance, and modern UI/UX patterns.

**Tools**: `["*"]`
**Allowed Tools**: `["read", "@git/git_status", "@git/git_log", "@fetch"]`

**Tool Settings**:
- **write**: Allowed paths include `src/ui/**`, `src/**/*.tsx`, `src/**/*.jsx`, `src/**/*.vue`, `src/**/*.svelte`, `src/**/*.css`, `src/**/*.scss`, `public/**`, `components/**`, `pages/**`, `styles/**`
- **shell**: Allowed commands include `npm test`, `npm run lint`, `npm run build`, `npm run dev`, `pnpm test`, `pnpm lint`, `yarn test`, `yarn lint`

**MCP Servers**:
- **git**: `git-mcp` with 120s timeout
- **fetch**: `fetch3.1` with 120s timeout
- **web-search**: Brave Search API with 120s timeout

**Tool Aliases**:
- `@git/git_status` → `status`
- `@git/git_log` → `log`

**Resources**: UI patterns, NiceGUI development, REST API patterns, code quality, testing, architecture development, README, package.json, tsconfig.json, vite.config.ts, tailwind.config.js

**Hooks**:
- **agentSpawn**: Shows git status and recent commits

### test-dev

**Description**: Multi-language test execution and quality analysis specialist. Handles Python (pytest, mypy, ruff), Rust (cargo test), JavaScript/TypeScript (npm test, jest), and general testing workflows.

**Tools**: `["read", "shell", "code"]`
**Allowed Tools**: `["read", "code"]`

**Tool Settings**:
- **shell**: Allowed commands include `pytest`, `mypy`, `ruff check`, `ruff format`, `cargo test`, `cargo clippy`, `npm test`, `npm run test`, `jest`, `go test`, `mvn test`, `gradle test`

**MCP Servers**: None

**Resources**: README, AGENTS.md, steering documents, pyproject.toml, Cargo.toml, package.json, test files

**Hooks**:
- **agentSpawn**: Counts test files in the project

### ssh-connection-expert

**Description**: Multi-hop SSH connection management and automation specialist

**Tools**: `["read", "write", "shell", "grep"]`
**Allowed Tools**: `["read", "shell", "grep"]`

**Tool Settings**:
- **shell**: Allowed commands include `ssh.*`, `ssh-keygen.*`, `ssh-add.*`, `ping.*`, `telnet.*`, `nc.*`
- **read**: Allowed paths include `src/core/connect/**`, `main_scan_cfg.json`, `main_scan_traffic_cfg.json`, `~/.ssh/**`

**MCP Servers**: None

**Resources**: Steering documents, connection code, configuration files, documentation

**Hooks**:
- **agentSpawn**: Shows loaded SSH keys

### project-test-runner

**Description**: Automated test execution and coverage analysis specialist

**Tools**: `["shell", "read", "write", "grep"]`
**Allowed Tools**: `["shell", "read", "grep"]`

**Tool Settings**:
- **shell**: Allowed commands include `uv run pytest.*`, `uv run mypy.*`, `uv run ruff.*`, `cargo test.*`, `npm test.*`
- **read**: Allowed paths include `tests/**`, `src/**`, `pyproject.toml`, `Cargo.toml`

**MCP Servers**: None

**Resources**: Steering documents, test files, source code, configuration files

**Hooks**:
- **agentSpawn**: Counts Python test files

### project-planner-git-workflow

**Description**: Specialized agent that are an expert on development workflow and handles Git integration for entire project

**Tools**: `["read", "write", "shell", "@git"]`
**Allowed Tools**: `["read", "@git/git_status", "@git/git_log", "@git/git_diff"]`

**Tool Settings**:
- **write**: Allowed paths include `src/**`, `tests/**`, `docs/**`, `*.md`, `*.json`, `package.json`, `requirements.txt`

**MCP Servers**:
- **git**: `git-mcp-server` with 30s timeout

**Tool Aliases**:
- `@git/git_status` → `status`
- `@git/git_log` → `log`
- `@git/git_diff` → `diff`

**Resources**: Research documents, documentation, README, TODO, source code, scripts, configuration files

**Hooks**:
- **agentSpawn**: Shows git status and current branch

### network-diagnostic-guru

**Description**: SSH-based network interface diagnostics and monitoring specialist for Interface Check project

**Tools**: `["read", "write", "shell", "grep", "glob"]`
**Allowed Tools**: `["read", "shell", "grep", "glob"]`

**Tool Settings**:
- **shell**: Allowed commands include `ssh.*`, `ethtool.*`, `mlxconfig.*`, `mlxlink.*`, `mst.*`, `ping.*`, `traceroute.*`, `netstat.*`, `ss.*`
- **read**: Allowed paths include `src/core/connect/**`, `src/platform/tools/**`, configuration files

**MCP Servers**: None

**Resources**: Steering documents, connection code, platform tools, traffic testing documentation, configuration files

**Hooks**:
- **agentSpawn**: Lists platform tool files

### hook-tester

**Description**: Minimal agent for testing hooks when updating Python files in scripts folder

**Tools**: `["read", "write"]`
**Allowed Tools**: `["read", "write"]`

**Tool Settings**:
- **write**: Allowed paths include `scripts/**/*.py`

**MCP Servers**: None

**Resources**: Script files

**Hooks**:
- **preToolUse**: Echo message before write operations
- **postToolUse**: Echo message after write operations

### documentation-specialist

**Description**: Technical documentation creation and maintenance expert

**Tools**: `["read", "write", "grep", "glob"]`
**Allowed Tools**: `["read", "write", "grep", "glob"]`

**Tool Settings**:
- **write**: Allowed paths include `docs/**`, `README.md`, `*.md`
- **read**: Allowed paths include `src/**`, `docs/**`, `*.md`, `*.json`, `pyproject.toml`

**MCP Servers**: None

**Resources**: Steering documents, documentation files, README, source code, configuration files

**Hooks**:
- **agentSpawn**: Counts markdown files in docs directory

### domain-finder

**Description**: Agent with access to domain search capabilities

**Tools**: `["@find-a-domain"]`
**Allowed Tools**: `["@find-a-domain"]`

**Tool Settings**: None

**MCP Servers**:
- **find-a-domain**: HTTP-based server at `https://api.findadomain.dev/mcp`

**Resources**: None

**Hooks**: None

### devops-infrastructure

**Description**: Docker, CI/CD, and deployment automation specialist

**Tools**: `["read", "write", "shell", "grep"]`
**Allowed Tools**: `["read", "shell", "grep"]`

**Tool Settings**:
- **shell**: Allowed commands include `docker.*`, `docker-compose.*`, `uv.*`, `git.*`
- **write**: Allowed paths include `Dockerfile`, `docker-compose.yml`, `.github/**`, `scripts/**`
- **read**: Allowed paths include `Dockerfile`, `docker-compose.yml`, `.github/**`, `scripts/**`, `pyproject.toml`

**MCP Servers**: None

**Resources**: Steering documents, Docker files, configuration files, scripts

**Hooks**:
- **agentSpawn**: Shows Docker version

### code-reviewer

**Description**: Code quality analysis and review specialist with security focus

**Tools**: `["read", "shell", "grep", "glob"]`
**Allowed Tools**: `["read", "shell", "grep", "glob"]`

**Tool Settings**:
- **shell**: Allowed commands include `uv run ruff check.*`, `uv run mypy.*`, `git diff.*`, `git log.*`, `find.*`, `wc.*`
- **read**: Allowed paths include `src/**`, `tests/**`, `*.py`, `*.md`, `pyproject.toml`

**MCP Servers**: None

**Resources**: Steering documents, source code, test files, configuration files, README

**Hooks**:
- **agentSpawn**: Shows recent git changes

### code-monkey-rust

**Description**: Fast, low-hallucination and correctness-first Rust agent. Specialized in rapid, bleeding edge development and strives to become a true Rust legend.

**Tools**: `["*"]`
**Allowed Tools**: `["read", "@git/git_status", "@git/git_log", "@fetch"]`

**Tool Settings**: None

**MCP Servers**:
- **find-a-domain**: HTTP-based server at `https://api.findadomain.dev/mcp` with 120s timeout
- **context7**: `uvx context7-mcp-server@latest` with 120s timeout
- **git**: `git-mcp` with 120s timeout
- **fetch**: `fetch3.1` with 120s timeout
- **web-search**: Brave Search API with 120s timeout

**Resources**: Research documents, documentation, README, TODO, Cargo.toml, Rust source files, scripts

**Hooks**: None

### code-monkey-python

**Description**: Fast, low-hallucination and correctness-first Python agent. Specialized in rapid, bleeding edge development and strives to become a Python legend.

**Tools**: `["*"]`
**Allowed Tools**: `["read", "@git/git_status", "@git/git_log", "@fetch"]`

**Tool Settings**: None

**MCP Servers**:
- **find-a-domain**: HTTP-based server at `https://api.findadomain.dev/mcp` with 120s timeout
- **context7**: `uvx context7-mcp-server@latest` with 120s timeout
- **git**: `git-mcp` with 120s timeout
- **fetch**: `fetch3.1` with 120s timeout
- **web-search**: Brave Search API with 120s timeout

**Resources**: Documentation, README, pyproject.toml, Python source files, scripts

**Hooks**:
- **postToolUse**: Auto-runs pytest after write operations

## Agent Categories

### Development Specialists
- **backend-dev**: Multi-language backend development
- **frontend-dev**: Modern frontend frameworks and UI/UX
- **code-monkey-python**: Rapid Python development
- **code-monkey-rust**: Rapid Rust development

### Testing & Quality
- **test-dev**: Multi-language test execution
- **project-test-runner**: Automated testing and coverage
- **code-reviewer**: Code quality and security analysis

### Infrastructure & Operations
- **devops-infrastructure**: Docker, CI/CD, deployment
- **ssh-connection-expert**: SSH connection management
- **network-diagnostic-guru**: Network interface diagnostics

### Project Management
- **project-planner-git-workflow**: Development workflow and Git
- **documentation-specialist**: Technical documentation

### Specialized Tools
- **domain-finder**: Domain search and availability
- **hook-tester**: Testing agent hooks functionality

## Common Patterns

### MCP Server Integration
- **git**: Git operations and repository management
- **fetch**: HTTP requests and API calls
- **web-search**: Brave Search API integration
- **context7**: Advanced context management
- **find-a-domain**: Domain search capabilities

### Tool Restrictions
- Most agents use `allowedTools` to restrict access to specific tools
- Shell commands are typically restricted to relevant operations
- File paths are limited to appropriate directories

### Hook Usage
- **agentSpawn**: Initialize agent with status information
- **postToolUse**: Auto-format or test after file operations
- **preToolUse**: Pre-operation validation or logging

## Security Considerations

1. **Tool Access**: Agents have restricted tool access via `allowedTools`
2. **Command Restrictions**: Shell commands limited to specific patterns
3. **Path Restrictions**: File operations restricted to relevant directories
4. **MCP Timeouts**: All MCP servers have appropriate timeout settings
5. **Environment Variables**: Sensitive data accessed via environment variables

## Usage Guidelines

1. **Choose Appropriate Agent**: Select based on task requirements
2. **Review Permissions**: Understand tool and path restrictions
3. **Monitor Resource Access**: Be aware of available resources
4. **Leverage MCP Servers**: Use integrated services when available
5. **Test Hooks**: Verify hook behavior in safe environments

## Version History

- v1.0 (2026-01-15 15:25:00): Initial comprehensive agents reference guide
- v1.1 (2026-01-15 16:01:00): Standardized field ordering across all agents (prompt after description)
- v1.2 (2026-01-15 16:03:00): Moved test-dev prompt to prompts/agents folder for consistency