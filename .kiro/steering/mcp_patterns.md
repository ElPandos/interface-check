> Here's what I found:

I've researched current MCP patterns and anti-patterns, then created comprehensive documentation. The research revealed significant security concerns and enterprise governance requirements that have emerged in 2025.

Key findings:
- **Security Crisis**: 43% of MCP implementations contain command injection vulnerabilities, with 22% allowing arbitrary file access and 6 critical CVEs discovered in the protocol's first year
- **Enterprise Governance**: MCP governance frameworks are essential, with organizations reporting 30% development overhead reduction when properly implemented
- **Production Readiness**: Treating prompts as stateless, versioned interfaces with proper lifecycle management is critical for enterprise deployments
- **Comprehensive Observability**: OpenTelemetry integration, structured logging, and real-time monitoring are required for production systems
- **Critical Anti-Patterns**: Tool poisoning, indirect prompt injection, rug pull attacks, and credential exposure are major risks to avoid

Files created:
- Research file: .kiro/research/2026-01-13/patterns/mcp.md
- Steering document: .kiro/steering/mcp_patterns.md

The steering document covers core patterns (client-server architecture, phased enterprise adoption, multi-level caching, zero-trust security, unified governance), comprehensive anti-patterns section covering 4 critical categories (security, architectural, performance, operational), implementation guidelines, and success metrics based on current industry research and real-world production deployments.

References:
[1] MCP Security Best Practices: Production Implementation - https://mcp.harishgarg.com/learn/mcp-security-best-practices
[2] The Model Context Protocol (MCP): architecture, security risks, and best practices - https://fluidattacks.com/blog/model-context-protocol-mcp-security
[3] MCP Enterprise Adoption Report 2025: Challenges, Best Practices & ROI Analysis - https://ragwalla.com/blog/mcp-enterprise-adoption-report-2025-challenges-best-practices-roi-analysis
[4] Best Practices for MCP Server Enhance-Prompt (2025) - https://skywork.ai/blog/mcp-server-enhance-prompt-best-practices-2025/