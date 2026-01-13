> Here's what I found:

I've researched current MCP patterns and anti-patterns, then created comprehensive documentation. The research revealed significant security concerns and enterprise adoption patterns that have emerged in 2025.

Key findings:
- **Security Crisis**: 43% of MCP implementations contain command injection vulnerabilities, with 22% allowing arbitrary file access
- **Enterprise Governance**: MCP governance frameworks are essential, with organizations reporting 30% development overhead reduction when properly implemented
- **Production Readiness**: Treating prompts as stateless, versioned interfaces with proper lifecycle management is critical
- **Performance Requirements**: Multi-level caching and connection pooling are essential for production deployments

Files created:
- Research file: .kiro/research/2026-01-13/patterns/mcp.md
- Steering document: .kiro/steering/mcp_patterns.md

The steering document covers essential patterns (server configuration, deployment, performance optimization, monitoring, security) and critical anti-patterns to avoid (security vulnerabilities, architectural mistakes, performance issues, operational problems) based on current industry research and real-world production deployments.

References:
[1] The Model Context Protocol (MCP): architecture, security risks, and best practices - https://fluidattacks.com/blog/model-context-protocol-mcp-security
[2] MCP Enterprise Adoption Report 2025: Challenges, Best Practices & ROI Analysis - https://ragwalla.com/blog/mcp-enterprise-adoption-report-2025-challenges-best-practices-roi-analysis
[3] Best Practices for MCP Server Enhance-Prompt (2025) - https://skywork.ai/blog/mcp-server-enhance-prompt-best-practices-2025/