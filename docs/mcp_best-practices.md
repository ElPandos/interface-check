---
title:        MCP Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# MCP Best Practices

## Core Principles

1. **Standardization Over Custom Integration**: Use MCP's JSON-RPC 2.0 specification as the single protocol for all AI-tool interactions. Avoid building custom connectors—expose tools once through MCP servers.

2. **Separation of Concerns**: Maintain clear boundaries between Host (conversation controller), Client (connection manager), and Server (capability provider). Each component has distinct responsibilities.

3. **Transport Agnosticism**: Design tools independent of transport layer. The same tool should work identically over STDIO (local), HTTP+SSE (remote), or WebSockets (real-time).

4. **Capability Discovery First**: Always implement dynamic capability negotiation. Agents should discover available tools, resources, and prompts at runtime rather than hardcoding.

5. **Stateful Context Management**: Design for multi-step workflows. Pass session context between steps to maintain coherence across long-running operations.

## Essential Practices

### Architecture Patterns

**Router Pattern** — Intelligent dispatcher that routes requests to appropriate backend services based on intent classification. Use when multiple specialized services exist.

**Tool Grouping Pattern** — Organize related tools into logical groups (e.g., `git/*`, `db/*`, `file/*`). Reduces cognitive load and enables granular permissions.

**Gateway Pattern** — Centralized MCP gateway for enterprise deployments:
- Single entry point for all MCP connections
- URL-based routing to internal/external servers
- Automatic credential management
- Centralized rate limiting and observability

**Single Endpoint Pattern** — Universal translator that normalizes diverse backend APIs into consistent MCP interface. Ideal for legacy system integration.

### Server Implementation

```python
# Minimal MCP-style tool server
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ToolInput(BaseModel):
    query: str

@app.post("/tools/search")
def search_tool(payload: ToolInput) -> dict:
    """Tool with clear input schema and structured output."""
    return {"results": [], "count": 0}

@app.get("/tools")
def list_tools() -> list[str]:
    """Dynamic capability discovery."""
    return ["search", "fetch", "analyze"]
```

### Client Connection

```python
# Connection with capability negotiation
async def connect_mcp(server_url: str) -> dict:
    """Initialize MCP session with handshake."""
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "capabilities": {"tools": {}, "resources": {}}
        }
    }
    # Server responds with its capabilities
    return await send_request(server_url, init_request)
```

### Security Implementation

- **Transport-Level**: Use TLS for HTTP/SSE; rely on OS process isolation for STDIO
- **Authentication**: OAuth 2.1 for remote servers; centralize credential management
- **Authorization**: Implement tool-level permissions with namespace isolation
- **User Consent**: Gate destructive operations behind explicit approval flows
- **Input Validation**: Validate all tool arguments against declared schemas

## Anti-Patterns to Avoid

1. **Custom Connector Proliferation**: Building separate integrations for each AI app × each tool creates N×M maintenance burden. Use MCP's standardized interface.

2. **Hardcoded Tool Lists**: Embedding available tools in application code prevents dynamic updates. Implement `tools/list` discovery.

3. **Stateless Multi-Step Workflows**: Losing context between tool calls breaks complex operations. Maintain session state across invocations.

4. **Trusting Tool Descriptions Blindly**: Tool descriptions from untrusted servers can be attack vectors. Validate server identity and implement introspection.

5. **Mixing Transport and Data Concerns**: Coupling tool logic to specific transport (STDIO vs HTTP) reduces portability. Keep them separate.

6. **Ignoring Capability Negotiation**: Skipping the initialize handshake leads to version mismatches and feature incompatibility.

7. **Exposing Raw Credentials**: Passing API keys through tool arguments. Use centralized credential management at gateway level.

## Implementation Guidelines

### Step 1: Server Setup
Choose transport based on deployment:
- **STDIO**: Local tools, IDE extensions, CLI assistants (microsecond latency)
- **HTTP+SSE**: Remote services, cloud deployments, web clients
- **WebSockets**: Real-time bidirectional, interactive scenarios

### Step 2: Define Primitives
- **Tools**: Executable actions with input/output schemas
- **Resources**: Read-only context (files, logs, schemas, configs)
- **Prompts**: Reusable instruction templates

### Step 3: Implement Lifecycle
```
initialize → capability negotiation → ready → [tool calls] → shutdown
```

### Step 4: Add Observability
- Log all tool invocations with request IDs
- Track latency per tool
- Monitor error rates and types
- Implement `$/progress` notifications for long operations

### Step 5: Security Hardening
- Namespace tools by team/service
- Implement rate limits per client
- Audit all capability access
- Sandbox local tool execution

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Discovery Time | < 100ms | Time from connect to tools/list response |
| Tool Invocation Latency | < 500ms (p95) | End-to-end tool call duration |
| Integration Reuse Rate | > 80% | Tools used by multiple agents |
| Error Rate | < 1% | Failed tool calls / total calls |
| Security Incidents | 0 | Unauthorized tool access attempts |
| Maintenance Overhead | -50% vs custom | Engineering hours per integration |

## Sources & References

- [Enterprise Architecture Patterns](https://doortoonline.com/blog/implementing-mcp-clients-at-scale-enterprise-architecture) — Centralized gateway, authentication patterns, standardization strategies (2025-07-12)
- [LLM Patterns: Routers, Tool Groups, Unified Endpoints](https://www.elasticpath.com/blog/mcp-magic-moments-guide-to-llm-patterns) — Four foundational MCP patterns for production systems (2025-10-20)
- [Protocol Mechanics and Architecture](https://pradeepl.com/blog/model-context-protocol/mcp-protocol-mechanics-and-architecture/) — JSON-RPC 2.0 foundation, transport layers, capability negotiation (2025-11-10)
- [Architecture, Components & Workflow](https://www.kubiya.ai/blog/model-context-protocol-mcp-architecture-components-and-workflow) — Host/Client/Server separation, primitives, migration strategy (2025-11-09)

Content was rephrased for compliance with licensing restrictions.

## Version History

- v1.0 (2025-01-13 00:00:00): Initial version based on 2024-2025 MCP architecture research
