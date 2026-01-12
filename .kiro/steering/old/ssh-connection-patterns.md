---
title: SSH Connection Patterns
inclusion: fileMatch
fileMatchPattern: 'src/core/connect/**/*.py'
---

# SSH Connection Patterns

## Connection Management
- **Connection Pooling**: Reuse SSH connections across components
- **Reconnection Logic**: Automatic reconnection with retry limits
- **Connection Status**: Visual indicators for connection health
- **Error Recovery**: Graceful handling of connection failures

## Multi-hop SSH
- **Jump Host Configuration**: Support for intermediate jump hosts
- **Connection Chaining**: Establish connections through multiple hops
- **Authentication**: Handle credentials for each hop separately
- **Timeout Management**: Appropriate timeouts for each connection level

## Security Best Practices
- **Credential Management**: Store SSH credentials securely
- **Key-based Authentication**: Prefer SSH keys over passwords
- **Connection Limits**: Implement connection pooling limits
- **Audit Logging**: Log all SSH connection attempts and failures

## Performance Optimization
- **Connection Reuse**: Share connections across multiple operations
- **Keepalive Settings**: Configure SSH keepalive to prevent timeouts
- **Parallel Operations**: Use connection pools for concurrent operations
- **Resource Cleanup**: Properly close connections and clean up resources

## Error Handling
- **Connection Failures**: Retry logic with exponential backoff
- **Authentication Errors**: Clear error messages for credential issues
- **Network Timeouts**: Appropriate timeout handling and user feedback
- **Host Key Verification**: Handle host key changes gracefully
