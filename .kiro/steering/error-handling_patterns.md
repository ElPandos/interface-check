> Here's what I found:

I've researched current error handling patterns and anti-patterns, then updated the existing steering document with comprehensive anti-patterns coverage. The research revealed significant evolution toward prevention-focused approaches and systematic anti-pattern recognition.

Key findings:
- **Prevention-focused error handling** emphasizes designing out problems rather than detecting them later
- **Exception swallowing and catch-all handlers** remain the most dangerous anti-patterns
- **Retry storms and timeout cascades** are common mistakes that can amplify failures
- **Resource leaks in error paths** continue to cause production issues
- **Modern resilience patterns** (circuit breaker, retry with backoff, bulkhead, timeout) are essential for distributed systems

File saved: .kiro/research/2026-01-13/patterns/error-handling.md
File updated: .kiro/steering/error-handling_patterns.md

The steering document now includes a comprehensive anti-patterns section covering the 10 most critical error handling anti-patterns to avoid, with practical examples of both problematic and correct implementations based on current 2024-2025 research.

## Synchronization Report (Tier 2)

### Primary File Updated
- Path: .kiro/steering/error-handling_patterns.md
- Change type: content enhancement with comprehensive anti-patterns section
- Impact: additive

### Related Files Identified
- .kiro/steering/error-handling_best-practices.md - reviewed (complementary focus on patterns vs best practices)
- .kiro/steering/testing_patterns.md - no change needed (error testing covered appropriately in both)
- .kiro/steering/security_patterns.md - no change needed (security error handling covered in both appropriately)

### Files Intentionally Not Checked
- Other pattern files (focus on different domains like UI, Docker, etc.)