---
title: Network Tools Integration
inclusion: always
---

# Network Tools Integration

## Tool Abstraction
- **Unified Interface**: Common interface for all network tools (ethtool, mlx, mst, rdma)
- **Command Builders**: Structured command construction with parameter validation
- **Output Parsing**: Dedicated parsers for each tool's output format
- **Error Handling**: Tool-specific error detection and recovery

## Execution Patterns
- **SSH Integration**: Remote tool execution via SSH connections
- **Local Execution**: Direct local tool execution with subprocess
- **Timeout Management**: Configurable timeouts for long-running operations
- **Retry Logic**: Automatic retry for transient failures

## Data Processing
- **Structured Output**: Convert raw tool output to typed data models
- **Value Parsing**: Extract numeric values with units (e.g., "10Gb/s" → 10000)
- **Status Detection**: Parse tool status indicators and error conditions
- **Data Validation**: Validate parsed data for consistency and completeness

## Tool-Specific Patterns
- **ethtool**: Interface statistics, link status, and configuration
- **mlxlink**: Mellanox link diagnostics and eye scan data
- **mlxconfig**: Adapter configuration and parameter management
- **mst**: Mellanox Software Tools integration
- **rdma**: RDMA interface monitoring and statistics

## Performance Optimization
- **Command Batching**: Execute multiple commands in single SSH session
- **Output Caching**: Cache tool output for repeated queries
- **Parallel Execution**: Run independent tool commands concurrently
- **Resource Management**: Limit concurrent tool executions

## Best Practices
- Use compiled regex patterns for parsing performance
- Implement tool availability checks before execution
- Handle tool version differences gracefully
- Log tool execution times for performance monitoring
- Validate tool prerequisites and permissions
