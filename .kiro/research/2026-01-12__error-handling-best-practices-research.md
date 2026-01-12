# Research Output – 2026-01-12 13:54 CET

## Original Prompt
> Can you research code error handling best practices? and use the research file to create a .kiro/steering/error-best-practices.md file

## Complete Response

Based on comprehensive research of current error handling best practices from industry experts, software pattern libraries, and production system experiences, here are the key findings for 2024-2026:

### Core Error Handling Principles

#### 1. Separation of Concerns
Error handling should be separated from normal business logic to improve code readability and maintainability. Exception handling allows programs to deal with anomalous conditions requiring special processing during execution.

#### 2. Systematic Approach
Error handling requires anticipating potential failures, providing meaningful feedback to users, and ensuring applications remain stable and secure. It's more than just catching exceptions - it's about building resilient systems.

#### 3. Layered Error Management
Different layers of a computer system define exceptions:
- CPU-defined interrupts
- Operating system signals  
- Programming language exceptions
Each layer requires different handling approaches, though they may be interrelated.

### Error Handling Patterns and Strategies

#### 1. Retry Pattern with Exponential Backoff
**Implementation**: 3-5 attempts with exponential backoff (1s, 2s, 4s, 8s, 16s)
**Best Practices**:
- Add random jitter to prevent thundering herd problems
- Don't retry authentication failures (wastes time)
- Don't retry rate limits unnecessarily
- Ensure operations are idempotent for safe retries
- Cap retry attempts and wait times

#### 2. Circuit Breaker Pattern
**Purpose**: Prevents cascading failures by stopping attempts to perform actions likely to fail
**States**:
- **Closed**: Normal operation, requests pass through
- **Open**: Failures exceed threshold, requests blocked with fallback response
- **Half-Open**: Single test request allowed to check if service recovered

**Configuration**: After N consecutive failures, stop trying for X minutes

#### 3. Graceful Degradation
**Approach**: When primary functionality fails, provide reduced but functional alternatives
**Implementation**: Return predefined fallback responses instead of complete failure
**Benefits**: Maintains service availability even during partial system failures

#### 4. Timeout Management
**Strategy**: Set appropriate timeouts for all operations to prevent indefinite blocking
**Best Practices**:
- Configure different timeout values for different operation types
- Implement timeout hierarchies (connection, request, total)
- Provide meaningful timeout error messages

### Logging and Monitoring Best Practices

#### 1. Structured Error Logging
**Essential Information**:
- Error types and stack traces
- Context information and timestamps
- User environment details
- Request/operation identifiers
- Correlation IDs for distributed systems

**Benefits**: Thorough logs reportedly decrease issue resolution time by up to 50%

#### 2. Log Level Strategy
- **Error**: For exceptions preventing method completion
- **Warning**: For recoverable issues that need attention
- **Info**: For important events like user request completion
- **Debug/Trace**: For detailed debugging during development

#### 3. Security Considerations
- **User-Facing Messages**: Generic, non-revealing ("An unexpected error occurred")
- **Internal Logs**: Detailed error information for developers
- **Never Expose**: Stack traces, database errors, or system details to users
- **Error Codes**: Use codes instead of detailed messages for tracking

### Exception Management Patterns

#### 1. Exception Hierarchy
**Design Principles**:
- Create custom exception classes for domain-specific errors
- Use proper inheritance hierarchy for exception types
- Categorize errors by type (network, validation, business logic)
- Implement consistent error codes for tracking

#### 2. Try-Catch-Finally Structure
**Best Practices**:
- Keep try blocks minimal and focused
- Catch specific exceptions rather than generic ones
- Use finally blocks for cleanup operations
- Avoid using exceptions for normal control flow

#### 3. Error Recovery Strategies
**Termination**: Shut down gracefully and hand control to OS
**Resumption**: Resume program execution near where exception occurred
**Compensation**: Undo partial operations and restore consistent state

### User Experience Considerations

#### 1. User-Friendly Error Messages
**Guidelines**:
- Provide clear, actionable error messages
- Include relevant context without technical details
- Suggest next steps when possible
- Maintain consistent tone and formatting

#### 2. Progress Indicators
**Implementation**:
- Show progress during long operations
- Provide feedback during error recovery attempts
- Display retry attempts and remaining time
- Allow user cancellation when appropriate

#### 3. Error Notifications
**Strategy**:
- Use appropriate UI notifications for different error types
- Distinguish between recoverable and non-recoverable errors
- Provide options for user action (retry, cancel, report)
- Maintain error state until user acknowledges

### Distributed Systems Error Handling

#### 1. Fault Tolerance Mechanisms
**Key Patterns**:
- Bulkhead isolation to prevent failure propagation
- Load balancing with health checks
- Service mesh for advanced error handling
- Chaos engineering for resilience testing

#### 2. Cascading Failure Prevention
**Strategies**:
- Implement circuit breakers between services
- Use timeouts and deadlines consistently
- Design for partial functionality during outages
- Monitor and alert on error rate thresholds

#### 3. Data Consistency
**Approaches**:
- Implement compensating transactions
- Use saga patterns for distributed transactions
- Design for eventual consistency
- Maintain audit trails for error recovery

### Performance and Resource Management

#### 1. Error Handling Overhead
**Optimization**:
- Minimize exception creation in hot paths
- Use error codes for expected failure cases
- Cache error messages and responses
- Implement efficient logging mechanisms

#### 2. Resource Cleanup
**Best Practices**:
- Use try-with-resources or context managers
- Implement proper disposal patterns
- Clean up resources in finally blocks
- Handle cleanup failures gracefully

#### 3. Memory Management
**Considerations**:
- Avoid memory leaks in error handling paths
- Limit error message and log sizes
- Implement log rotation and archival
- Monitor memory usage during error conditions

### Testing Error Handling

#### 1. Error Injection Testing
**Techniques**:
- Simulate network failures and timeouts
- Test with invalid inputs and edge cases
- Verify error recovery mechanisms
- Validate user experience during errors

#### 2. Chaos Engineering
**Practices**:
- Introduce controlled failures in production
- Test system resilience under stress
- Validate monitoring and alerting systems
- Measure recovery times and user impact

### Modern Error Handling Trends (2024-2026)

#### 1. Error Model Convergence
Languages like C++, JavaScript, Python, Java, and C# have converged on similar throw/catch/finally constructs with equivalent runtime semantics and typing rules.

#### 2. Functional Error Handling
Growing adoption of Result/Option types in languages that support them, moving away from exceptions for expected error cases.

#### 3. Observability Integration
Error handling increasingly integrated with observability platforms for better monitoring, tracing, and debugging capabilities.

#### 4. AI-Assisted Error Recovery
Emerging patterns use AI assistance to implement sophisticated recovery patterns that minimize downtime and maintain service quality.

## Key Findings

- Error handling requires systematic approach beyond just catching exceptions
- Retry with exponential backoff and circuit breakers are critical resilience patterns
- Structured logging with proper security considerations essential for debugging
- User experience must be considered in error handling design
- Modern systems converge on similar error handling patterns across languages
- Testing and chaos engineering crucial for validating error handling effectiveness

## Sources & References

- [Error Handling and Recovery Patterns](https://softwarepatternslexicon.com/stream-processing/error-handling-and-recovery-patterns/error-logging/) — Comprehensive error logging patterns
- [12 Error Logging Best Practices 2024](https://tryhoverify.com/blog/12-error-logging-best-practices-2024) — Current logging best practices
- [Error Handling and Reliability Patterns for Production AI Agents](https://getathenic.com/blog/error-handling-reliability-patterns-production-ai-agents) — Modern resilience patterns
- [Circuit Breaker vs. Retry Pattern](https://www.geeksforgeeks.org/circuit-breaker-vs-retry-pattern/) — Pattern comparison and implementation
- [The Second Great Error Model Convergence](https://matklad.github.io/2025/12/29/second-error-model-convergence.html) — Modern error handling evolution

## Tools & Methods Used

- web_search: "error handling best practices 2024 2025 programming exception management"
- web_search: "error handling best practices logging recovery patterns 2024"
- web_search: "error handling patterns retry circuit breaker graceful degradation 2024"

## Metadata

- Generated: 2026-01-12T13:54:15+01:00
- Model: Claude 3.5 Sonnet
- Session ID: N/A
- Tool calls total: 3
- Approximate duration: ~4 minutes

## Limitations & Confidence Notes

- Data current as of January 2026 – error handling practices continue evolving
- Focus on general patterns – specific language implementations may vary
- Emphasis on distributed systems – monolithic applications may need different approaches
- Security considerations based on current threat landscape
- Recommended next steps: Implement patterns incrementally and measure effectiveness in production
