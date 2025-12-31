---
title: Error Handling Patterns
inclusion: always
---

# Error Handling Patterns

## Exception Hierarchy
- **Custom Exceptions**: Define project-specific exception classes
- **Exception Inheritance**: Use proper exception inheritance hierarchy
- **Error Categories**: Categorize errors by type (network, config, validation)
- **Error Codes**: Use consistent error codes for different error types

## Error Recovery
- **Retry Logic**: Implement retry logic with exponential backoff
- **Circuit Breaker**: Use circuit breaker pattern for external services
- **Graceful Degradation**: Continue operation with reduced functionality
- **Fallback Mechanisms**: Provide fallback options when primary fails

## User Experience
- **User-Friendly Messages**: Provide clear, actionable error messages
- **Error Context**: Include relevant context in error messages
- **Progress Indicators**: Show progress during long operations
- **Error Notifications**: Use appropriate UI notifications for errors

## Logging and Debugging
- **Error Logging**: Log all errors with appropriate detail
- **Stack Traces**: Include stack traces for debugging
- **Error Correlation**: Correlate related errors across components
- **Debug Information**: Collect debug information for troubleshooting

## Network Error Handling
- **Connection Failures**: Handle SSH connection failures gracefully
- **Timeout Handling**: Appropriate timeout handling for network operations
- **Authentication Errors**: Clear handling of authentication failures
- **Host Unreachable**: Handle network unreachability scenarios

## Validation Errors
- **Input Validation**: Validate all user inputs before processing
- **Configuration Validation**: Validate configuration files on load
- **Data Validation**: Validate data from external sources
- **Type Validation**: Use type hints and runtime validation

## Resource Management
- **Resource Cleanup**: Ensure proper cleanup on errors
- **Memory Management**: Handle memory errors and cleanup
- **File Handle Management**: Proper file handle cleanup on errors
- **Connection Cleanup**: Clean up network connections on errors
