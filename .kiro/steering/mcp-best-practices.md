---
title:        MCP Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-12
status:       active
---

# MCP Best Practices

## Purpose
Establish standardized Model Context Protocol (MCP) server configuration and usage practices for secure, scalable, and maintainable AI integrations.

## Core Principles

### 1. Server Architecture
- **Single Purpose**: Each MCP server should have one clear, well-defined purpose
- **Stateless Design**: Design servers as focused, stateless services for scalability
- **Containerization**: Use Docker containers for consistent deployment and isolation
- **Infrastructure as Code**: Automate deployment with templated provisioning
- **Configuration Management**: Use schemas and templates for consistent setup

### 2. Security and Authentication
- **OAuth 2.1**: Use modern OAuth 2.1 for HTTP-based transports (replacing API keys)
- **Role-Based Access Control**: Implement fine-grained permissions and user context
- **Least Privilege**: Grant minimum necessary permissions for functionality
- **Multi-Factor Authentication**: Require MFA for administrative actions
- **Session Security**: Generate non-predictable session IDs and validate context
- **Credential Rotation**: Regular review and rotation of authentication credentials

### 3. Data Protection
- **Encryption in Transit**: Use TLS 1.3 for all communications
- **Encryption at Rest**: Use AES-256 for sensitive data storage
- **Certificate Management**: Proper SSL/TLS certificate validation and rotation
- **Protocol Migration**: Move away from deprecated protocols (DES, SMBv1, NTLM)
- **Secure Boot Planning**: Prepare for certificate expiration in 2026

## Server Configuration

### 1. Workspace-Level Configuration
- Use `.kiro/settings/mcp.json` for project-specific servers
- Use `~/.kiro/settings/mcp.json` for global/cross-workspace servers
- Workspace config takes precedence over user config for conflicts
- Always specify exact versions or use `@latest` for stability

### 2. Installation and Setup
- Use `uvx` command for Python-based MCP servers (requires `uv` package manager)
- Install `uv` via pip, homebrew, or official installation guide
- No separate installation needed for uvx servers - they download automatically
- Test servers immediately after configuration

### 3. Security and Auto-Approval
- Use `autoApprove` sparingly and only for trusted, low-risk tools
- Review tool capabilities before adding to auto-approve list
- Regularly audit auto-approved tools for security implications
- Consider environment-specific auto-approve settings

## Monitoring and Observability

### 1. Logging Requirements
- **Continuous Activity Logging**: Log all MCP server interactions
- **Structured Logging**: Use correlation IDs and consistent formats
- **Essential Log Fields**: User identity, timestamp, action, data source, outcome
- **Centralized Logging**: Use MCP gateways for policy enforcement
- **Audit Trail**: Maintain compliance-ready audit logs

### 2. Performance Monitoring
- **Real-time Monitoring**: Monitor for anomalies and performance issues
- **Resource Utilization**: Track CPU, memory, and I/O usage
- **Performance Metrics**: Monitor latency, error rates, and throughput
- **Load Balancing**: Implement routing rules and horizontal scaling
- **Auto-scaling**: Dynamic resource adjustment based on demand

### 3. Error Handling and Debugging
- Set `FASTMCP_LOG_LEVEL: "ERROR"` to reduce noise in logs
- Use `disabled: false` to temporarily disable problematic servers
- Servers reconnect automatically on configuration changes
- Use MCP Server view in Kiro feature panel for manual reconnection

## Common MCP Server Examples

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    },
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": ["read_file", "list_directory"]
    }
  }
}
```

## Scalability and Performance

### 1. Resource Requirements
- **Memory**: 16 GB RAM minimum
- **CPU**: Quad-core processor minimum
- **Storage**: 512 GB SSD minimum
- **Network**: High-throughput, low-latency connectivity

### 2. Deployment Models
- **Managed Platforms**: Use fully-managed MCP services for enterprise
- **Hybrid Environments**: Combine on-premises and cloud resources
- **Pay-as-you-go**: Cloud-based scaling without upfront investment
- **Containerized Deployment**: Use Docker for consistent environments

### 3. Performance Optimization
- **Caching Strategies**: Optimize performance while maintaining security
- **Load Balancing**: Distribute requests across multiple server instances
- **Resource Monitoring**: Benchmark performance under realistic AI workloads
- **Horizontal Scaling**: Plan for growth with auto-scaling capabilities

## Development Workflow

### 1. Testing and Validation
- Test MCP tools immediately after configuration
- Don't inspect configurations unless facing specific issues
- Use sample calls to verify tool behavior
- Test with various parameter combinations
- Document working examples for team reference

### 2. Deployment Automation
- **CI/CD Integration**: Automated deployment pipelines
- **Configuration Templates**: Provide deployment templates and schemas
- **Post-deployment Testing**: Automated validation after deployment
- **Version Management**: Treat prompts as stateless, versioned interfaces

### 3. Documentation and Support
- **Comprehensive Guides**: Setup, usage, and troubleshooting documentation
- **Configuration Schemas**: Well-defined configuration structures
- **Team Training**: Regular training on MCP best practices
- **Knowledge Sharing**: Document working patterns and solutions

## Maintenance and Updates

### 1. Regular Maintenance
- **Prompt Updates**: Apply MCP server updates promptly
- **Dependency Management**: Track and update dependencies regularly
- **Security Patches**: Maintain up-to-date software components
- **Performance Tuning**: Regular performance review and optimization

### 2. Migration and Upgrades
- **Deprecated Features**: Proactive transition from deprecated components
- **Version Planning**: Plan for major version upgrades
- **Backup Strategies**: Maintain configuration backups before changes
- **Rollback Procedures**: Prepare rollback plans for failed updates

## Troubleshooting

### 1. Common Issues
- Check server logs in Kiro's MCP Server view
- Verify `uv` and `uvx` installation if Python servers fail
- Test server connectivity outside of Kiro if needed
- Use command palette "MCP" commands for server management
- Restart servers via MCP Server view rather than restarting Kiro

### 2. Permission Issues
- Add permission rules to Claude Code settings (`.claude/settings.json`)
- Use `"permissions": {"allow": ["Bash(**/mcp-server/**)"]}` for bash commands
- Review and adjust auto-approve settings for security
- Validate user context and role-based permissions

## Best Practices for Tool Usage

### 1. Tool Integration
- Understand tool capabilities before first use
- Use descriptive prompts when calling MCP tools
- Handle tool errors gracefully in workflows
- Combine multiple MCP tools for complex tasks
- Cache results when appropriate to avoid repeated calls

### 2. Development Integration
- Use Context7 MCP server to verify dependency compatibility
- Leverage AWS-Knowledge MCP server for current documentation
- Use aws-api-mcp-server for AWS API interactions
- Reference official sources through MCP servers when available

## Version History

- v1.0 (2026-01-12): Initial version based on industry best practices and enterprise deployment patterns
