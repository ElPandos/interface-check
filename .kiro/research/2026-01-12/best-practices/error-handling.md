# Research Output – 2026-01-12 23:58 CET

## Original Prompt
> Research best error handling practices. Use the research file to create/update .kiro/steering/error-handling_best-practices.md

## Complete Response

Based on comprehensive research of current industry practices, here are the essential error handling best practices for 2025:

### Core Resilience Principles

**Fail Fast vs Graceful Degradation Balance**:
- Fail fast for critical errors that cannot be recovered from
- Graceful degradation for partial failures where core functionality can continue
- Design systems to isolate failures and prevent cascading effects
- Build autonomous recovery mechanisms wherever possible

**Defense in Depth Strategy**:
- Multiple layers of error handling across network, application, and data layers
- Redundant safeguards so if one mechanism fails, others provide backup
- Comprehensive coverage addressing different failure modes
- Proactive prevention combined with reactive response

**Assume Breach Mentality**:
- Design for failure as the default state, not the exception
- Build systems that gracefully degrade rather than dramatically collapse
- Implement spectrum management for partial degradation, not binary up/down states
- Plan for network unreliability, service failures, and resource contention

### Essential Resilience Patterns

**Circuit Breaker Pattern**:
- Monitor service health and response times continuously
- Three states: Closed (normal), Open (failing), Half-Open (testing recovery)
- Failure thresholds: ≥50% failure rate over 50 calls or consecutive failures ≥K
- Automatic recovery testing after timeout periods (typically 30-300 seconds)
- Prevent retry storms and cascading failures

**Retry with Exponential Backoff**:
- Standard progression: 1s, 2s, 4s, 8s, 16s with jitter to prevent thundering herd
- Limit retry attempts to 3-5 maximum to avoid infinite loops
- Only retry transient errors, not client errors (4xx) or non-idempotent operations
- Implement idempotency keys to safely retry operations without side effects

**Bulkhead Pattern**:
- Isolate resources to prevent failure propagation
- Separate thread pools for different service types
- Isolated connection pools for different databases
- Resource quotas for different user tiers or request types
- Queue-based isolation for different message types

**Timeout Management**:
- Connection timeouts: 5-10 seconds for establishing connections
- Request timeouts: Variable based on operation complexity
- Use percentile-based timeouts (p99 latency + buffer)
- Implement deadline propagation to pass remaining time budget downstream

### Advanced Error Handling Patterns

**Dead Letter Queue (DLQ) Pattern**:
- Capture messages that cannot be processed after maximum retry attempts
- Include original message, error details, retry count, and timestamps
- Implement manual review and reprocessing capabilities
- Monitor DLQ depth as key operational metric

**Idempotency Implementation**:
- Generate unique idempotency keys for operations
- Store operation results with keys to prevent duplicate processing
- Use pessimistic locking to ensure exclusive access during processing
- Return cached results for duplicate requests

**Saga Pattern for Distributed Transactions**:
- Choreography: Services coordinate through events
- Orchestration: Central coordinator manages transaction flow
- Compensation: Rollback mechanisms for failed transactions
- Maintain transaction state and enable recovery from partial failures

**Graceful Degradation Strategies**:
- Cache fallback: Serve stale data when fresh data unavailable
- Static fallback: Return default values or simplified responses
- Service fallback: Use alternative services when primary fails
- Feature degradation: Disable non-essential features while maintaining core functionality

### Observability and Monitoring

**Structured Error Logging**:
- Include correlation IDs for tracking requests across distributed systems
- Capture error context: user journey, system state, and environmental factors
- Use consistent log formats for searchability and analysis
- Implement proper log levels and avoid exposing sensitive information

**Key Metrics to Monitor**:
- Error rates: Percentage of requests resulting in errors
- Retry success rates: Effectiveness of retry mechanisms
- Circuit breaker states: Frequency of trips and recoveries
- Timeout rates: Operations exceeding timeout thresholds
- DLQ depth: Number of messages requiring manual intervention

**Alerting Strategies**:
- Set thresholds based on business impact (e.g., 5% error rate, 10% timeout rate)
- Implement escalation procedures for different severity levels
- Use anomaly detection for unusual patterns
- Provide actionable alerts with clear remediation steps

### Implementation Guidelines

**Error Classification**:
- Transient errors: Network timeouts, temporary service unavailability → Retry with backoff
- Persistent errors: Invalid input, authentication failures → Return error immediately
- System errors: Infrastructure failures, resource exhaustion → Circuit break and fallback
- Client errors: Bad requests, validation failures → Return descriptive error message

**Testing Error Scenarios**:
- Chaos engineering: Randomly inject failures for testing
- Network failures: Simulate connection timeouts and packet loss
- Service degradation: Test with slow or partially failing services
- Resource exhaustion: Test behavior under memory or CPU pressure
- Data corruption: Test handling of malformed or invalid data

**Team Practices**:
- Include error scenarios in code reviews
- Maintain clear documentation of error handling patterns
- Regular team training on error handling best practices
- Established procedures for handling production errors
- Post-mortem analysis to learn from failures and improve handling

### Modern Error Handling Technologies

**AI-Assisted Error Detection**:
- Pattern recognition for identifying architectural and performance risks
- Context-aware analysis of changes with repository-wide understanding
- Automated risk scoring to surface high-risk changes for human review
- Learning from historical issues to prevent similar problems

**Production Monitoring Tools**:
- Application Performance Monitoring (APM) for comprehensive tracking
- Distributed tracing for microservices performance analysis
- Real User Monitoring (RUM) for actual user experience measurement
- Synthetic monitoring for proactive issue detection

## Key Findings

- **Graceful degradation** is preferred over fail-fast for user-facing systems, maintaining core functionality during partial failures
- **Circuit breaker pattern** is essential for preventing cascading failures in distributed systems, with 50% failure rate thresholds being standard
- **Exponential backoff with jitter** prevents retry storms, using 1s, 2s, 4s, 8s, 16s progression with 3-5 maximum attempts
- **Idempotency** is critical for safe retries in distributed systems, requiring unique keys and result caching
- **Observability** through structured logging and comprehensive monitoring is fundamental for effective error handling
- **Dead letter queues** provide essential safety nets for message processing failures, requiring manual review processes

## Sources & References

- [Error handling in distributed systems: A guide to resilience patterns - Temporal](https://temporal.io/blog/error-handling-in-distributed-systems) — Comprehensive guide to building resilient distributed systems - accessed 2026-01-12
- [Building Resilient ASP.NET Core Apps with Circuit Breakers - ASP Today](https://www.asptoday.com/p/building-resilient-aspnet-core-applications) — Foundation patterns for resilient applications - accessed 2026-01-12
- [Practical Resilience Patterns and the Promise of Durable Execution - Bix Tech](https://bix-tech.com/error-handling-in-distributed-systems-practical-resilience-patterns-and-the-promise-of-durable-execution/) — Practical implementation of resilience patterns - accessed 2026-01-12
- [Top Resiliency Patterns for Scaled Microservices - Hokstad Consulting](https://hokstadconsulting.com/blog/top-resiliency-patterns-for-scaled-microservices) — Timeout, circuit breaker, and retry patterns - accessed 2026-01-12
- [Circuit Breaker, Bulkhead, Retry, and Timeout for Building Resilient Microservices - Dev Nexus Hub](https://umamahesh.net/resiliency-patterns-circuit-breaker-bulkhead-retry-and-timeout-for-building-resilient-microservices/) — Comprehensive resilience pattern implementation - accessed 2026-01-12
- [A guide to graceful degradation in web development - LogRocket](https://blog.logrocket.com/guide-graceful-degradation-web-development/) — Graceful degradation principles and implementation - accessed 2026-01-12

## Tools & Methods Used

- web_search: "error handling best practices 2025 resilient applications fault tolerance patterns"
- web_search: "error handling best practices 2025 circuit breaker retry patterns bulkhead timeout"
- web_search: "error handling best practices 2025 graceful degradation fallback strategies observability monitoring"
- web_search: "error handling best practices 2025 dead letter queue idempotency saga pattern distributed transactions"

## Metadata

- Generated: 2026-01-12T23:58:05+01:00
- Model: Claude 3.5 Sonnet
- Tags: error-handling, resilience-patterns, circuit-breaker, retry-patterns, graceful-degradation, fault-tolerance, distributed-systems
- Confidence: High - based on current industry research and established resilience engineering practices
- Version: 1

## Limitations & Confidence Notes

- Data current as of January 2026
- Error handling strategies should be adapted to specific application contexts and failure modes
- Implementation approaches may vary based on technology stack and organizational requirements
- Regular testing and monitoring essential for validating error handling effectiveness
- Next steps: Team-specific customization and gradual adoption of resilience patterns
