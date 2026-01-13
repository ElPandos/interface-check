> Here's what I found:

I've researched current error handling best practices and created comprehensive documentation. The research revealed significant evolution toward systematic resilience patterns, structured observability, and proactive failure management.

Key findings:
- **Prevention-focused approach** emphasizes designing out problems rather than detecting them later
- **Structured logging** reduces troubleshooting time by 50% through JSON-formatted logs with consistent fields
- **Circuit breaker patterns** are essential for preventing cascading failures in distributed systems
- **Error categorization** (transient, persistent, system, client) enables appropriate response strategies
- **70% of software failures** stem from inadequate error management, making systematic approaches critical

File saved: .kiro/research/2026-01-13/best-practices/error-handling.md
File created: .kiro/steering/error-handling_best-practices.md

The steering document covers core principles (fail fast/safe, defense in depth, observability-first), essential resilience patterns (circuit breaker, retry with backoff, timeout management, bulkhead), structured error handling with categorization, observability integration, implementation guidelines, and common anti-patterns based on current industry research.

References:
[1] Error handling in distributed systems: A guide to resilience patterns - https://temporal.io/blog/error-handling-in-distributed-systems
[2] Building Bulletproof Software by Using Error Handling - https://www.iteratorshq.com/blog/building-bulletproof-software-by-using-error-handling/
[3] Building Robust Web Services with Error Management Techniques - https://moldstud.com/articles/p-building-resilient-web-services-effective-techniques-for-error-management
[4] Error Handling Standards: Ensuring Resilient Cloud Applications - https://softwarepatternslexicon.com/cloud-computing/api-management-and-integration-services/error-handling-standards/
[5] Building Production-Ready Resilient Distributed Systems - https://blog.shellnetsecurity.com/posts/2025/building-resilient-systems-with-ai-and-automation/
[6] Error Logging Best Practices - https://jakubkrajewski.substack.com/p/error-logging-best-practices
[7] Error Handling in Java EE Best Logging Monitoring Techniques - https://moldstud.com/articles/p-effective-error-handling-in-java-ee-best-logging-and-monitoring-techniques