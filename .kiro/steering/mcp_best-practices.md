> Here's what I found:

I've researched current MCP best practices and created comprehensive documentation. The research revealed significant security concerns and enterprise governance requirements that have emerged in 2025.

Key findings:
- **Security Crisis**: 43% of MCP implementations contain command injection vulnerabilities, with 22% allowing arbitrary file access and 6 critical CVEs discovered in the protocol's first year
- **Enterprise Governance**: MCP governance frameworks are essential, with organizations reporting 30% development overhead reduction when properly implemented
- **Production Readiness**: Treating prompts as stateless, versioned interfaces with proper lifecycle management is critical for enterprise deployments
- **Comprehensive Observability**: OpenTelemetry integration, structured logging, and real-time monitoring are required for production systems
- **Critical Anti-Patterns**: Tool poisoning, indirect prompt injection, rug pull attacks, and credential exposure are major risks to avoid

Files created:
- Research file: .kiro/research/2026-01-13/best-practices/mcp.md
- Steering document: .kiro/steering/mcp_best-practices.md

The steering document covers security-first architecture, enterprise governance frameworks, production deployment patterns, performance optimization, observability integration, critical anti-patterns to avoid, and comprehensive implementation guidelines based on current industry research and real-world production deployments.

References:
[1] MCP Security Best Practices: Production Implementation - https://mcp.harishgarg.com/learn/mcp-security-best-practices
[2] MCP Implementation: Production Deployment Guide 2025 - https://mcp.harishgarg.com/learn/mcp-implementation-checklist-complete-guide
[3] Best Practices for MCP Server Enhance-Prompt (2025) - https://skywork.ai/blog/mcp-server-enhance-prompt-best-practices-2025/
[4] The 10 MCP Security Risks Enterprise Teams Are Underestimating - https://www.webrix.ai/blog/10-mcp-security-risks-enterprise-teams-underestimating
[5] MCP is fueling agentic AI — and introducing new security risks - https://www.csoonline.com/article/4015222/mcp-uses-and-risks.html